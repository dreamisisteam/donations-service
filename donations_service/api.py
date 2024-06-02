from typing import Any

from ninja import NinjaAPI, ModelSchema
from ninja.pagination import paginate, PageNumberPagination

from donations_service import models

api = NinjaAPI()


class MemberSchema(ModelSchema):
    """ Member schema """
    avatar_url: str | None = None
    needs: list[dict[str, Any]] | None = None

    class Meta:
        model = models.Member
        fields = ('id', 'address', 'charges',
                  'description', 'tags', 'user',)


@api.get('/members', response=list[MemberSchema])
@paginate(PageNumberPagination, page_size=5)
def get_members(request):
    return models.Member.objects.all()
