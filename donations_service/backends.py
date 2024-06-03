import logging

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from donations_service import gateways, models

logger = logging.getLogger(__name__)


class TokenBackend(ModelBackend):
    """Backend to provide auth using address-key pair"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate user by blockchain role"""
        private_key = password

        try:
            address = gateways.w3.eth.account.from_key(private_key).address.lower()
            superuser_address = gateways.contracts_gateway.owner

            is_superuser = address == superuser_address
            is_member = address in gateways.contracts_gateway.members
        except Exception as ex:
            logger.exception(ex)
            return None

        if not (is_staff := is_superuser or is_member):
            return None

        first_name, last_name = username.split(" ")
        details_user_info = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": True,
            "is_superuser": is_superuser,
            "is_staff": is_staff,
        }

        if is_member:
            member, _ = models.Member.objects.get_or_create(
                address=address,
            )  # get member by address

            if user := member.user:
                for attr, value in details_user_info.items():
                    setattr(user, attr, value)
                user.save()  # update user obj if exists
            else:
                user = get_user_model().objects.create(**details_user_info)
                member.user = user
                member.save()  # create user obj if not exists and update member

            return user

        elif is_superuser:
            return get_user_model().objects.update_or_create(
                is_superuser=True, defaults=details_user_info
            )[0]

        else:
            return None
