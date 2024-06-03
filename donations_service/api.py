from typing import Any

from django.conf import settings
from django.contrib.auth.models import User

from ninja import NinjaAPI, Schema, ModelSchema
from ninja.pagination import paginate, PageNumberPagination

from donations_service import models, gateways

api = NinjaAPI()


class NestedUserSchema(ModelSchema):
    """Nested user representation for Member schema"""

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
        )


class MemberSchema(ModelSchema):
    """Member schema"""

    user: NestedUserSchema | None
    avatar_url: str | None = None
    needs: list[dict[str, Any]] | None = None

    class Meta:
        model = models.Member
        fields = (
            "id",
            "address",
            "charges",
            "total",
            "description",
            "tags",
            "user",
        )


class NetworkSchema(Schema):
    """Network schema"""

    contract_address: str
    exchanger_contract_abi: list[dict]
    token_contract_abi: list[dict]


@api.get("/members", response=list[MemberSchema])
@paginate(PageNumberPagination, page_size=5)
def get_members(request):
    """Get members list"""
    return models.Member.objects.all().active()


@api.get("/network", response=NetworkSchema)
def get_network_schema(request):
    """Get network info"""
    return {
        "contract_address": settings.CONTRACT_ADDRESS,
        "exchanger_contract_abi": gateways.contracts_gateway.exchanger.abi,
        "token_contract_abi": gateways.contracts_gateway.token.abi,
    }
