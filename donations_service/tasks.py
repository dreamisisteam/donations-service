import logging
import pprint
from typing import Callable, Any

import dramatiq

from django.contrib.auth import get_user_model
from django.core.cache import cache

from dramatiq_crontab import cron

from donations_service import models, gateways

logger = logging.getLogger(__name__)


@cron("*/3 * * * *")
@dramatiq.actor
def sync_members_registry(*args, **kwargs):
    """Sync members registry state"""
    return _common_task(sync_members_registry, _sync_members_registry, *args, **kwargs)


@cron("*/1 * * * *")
@dramatiq.actor
def sync_members_needs(*args, **kwargs):
    """Sync members needs"""
    return _common_task(sync_members_needs, _sync_members_needs, *args, **kwargs)


def _sync_members_registry():
    cache.delete("donation_members")  # clear registry from cache

    users_id_by_address_mapping = dict(
        models.Member.objects.values_list("address", "user__id")
    )

    existing_members_set = set(users_id_by_address_mapping.keys())
    contract_members_set = set(gateways.contracts_gateway.members)

    new_members_addresses = contract_members_set - existing_members_set
    deactivated_members_addresses = existing_members_set - contract_members_set
    actual_existing_members_addresses = (
        existing_members_set - deactivated_members_addresses
    )

    logger.info("New members to create: %s", len(new_members_addresses))
    logger.info("Members to deactivate: %s", len(deactivated_members_addresses))
    logger.info("Existing actual members: %s", len(actual_existing_members_addresses))

    # deactivate users objs
    get_user_model().objects.filter(
        id__in=[
            users_id_by_address_mapping[deactivated_member_address]
            for deactivated_member_address in deactivated_members_addresses
        ]
    ).update(is_active=False, is_staff=True)

    # activate actual users
    get_user_model().objects.filter(
        id__in=[
            users_id_by_address_mapping[actual_existing_member_address]
            for actual_existing_member_address in actual_existing_members_addresses
        ]
    ).update(is_active=True, is_staff=True)

    # create new members
    members_objs_to_create = []
    for address in new_members_addresses:
        members_objs_to_create.append(models.Member(address=address))

    models.Member.objects.bulk_create(members_objs_to_create, batch_size=100)


def _sync_members_needs():
    members_queryset = (
        models.Member.objects.select_related("user")
        .only("address", "needs", "charges", "user__is_active")
        .active()
    )

    members_to_update_objs: list[models.Member] = []
    for member_obj in members_queryset.iterator(chunk_size=100):
        needs_info, charges, total = gateways.contracts_gateway.get_member_needs_state(
            member_obj.address
        )

        member_obj.needs = needs_info
        member_obj.charges = charges
        member_obj.total = total

        members_to_update_objs.append(member_obj)

    logger.info("Members needs to update: %s", len(members_to_update_objs))
    models.Member.objects.bulk_update(
        members_to_update_objs, fields=["needs", "charges", "total"], batch_size=100
    )


def _common_task(task, task_function: Callable, *args, **kwargs) -> Any:
    if args and args[0] is None:
        args = list(args)
        args.pop(0)

    logger.info(
        "================ START TASK %s ================\nargs: %s\nkwargs: %s",
        task.actor_name,
        pprint.pformat(args),
        pprint.pformat(kwargs),
    )

    try:
        return task_function(*args, **kwargs)
    except Exception as ex:  # pylint: disable=broad-except
        logger.exception(ex)
        return None
    finally:
        logger.info("================ END TASK %s ================", task.actor_name)
