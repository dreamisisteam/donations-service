from django.db.models import QuerySet


class MembersQuerySet(QuerySet):
    """ QuerySet for Members Model """

    def active(self, reverse: bool = False):
        """
        Returns active members
        :param reverse: return inactive members?
        :return: active members queryset
        """
        return self.filter(user__is_active=not reverse)
