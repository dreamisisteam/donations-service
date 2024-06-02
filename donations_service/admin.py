from django.contrib import admin

from donations_service import models


class MemberIsActiveFilter(admin.SimpleListFilter):
    """ Filter of members active state """
    title = 'Is active?'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            (1, 'Yes'),
            (0, 'No'),
        )

    def queryset(self, request, queryset):
        if not (value := self.value()):
            return queryset

        filter_function = 'filter' if bool(int(value)) else 'exclude'
        return getattr(queryset, filter_function)(user__is_active=True)


@admin.register(models.Member)
class MemberAdmin(admin.ModelAdmin):
    """ Admin representation of Member model """
    fields = ('address', 'needs', 'charges', 'description',
              'tags', 'user', 'avatar',)
    readonly_fields = ('address',)
    autocomplete_fields = ('user',)

    list_display = ('address', 'user__is_active',)
    list_filter = (MemberIsActiveFilter,)

    search_fields = ('address', 'user__username',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        is_list_request = request.path.strip('/').split('/')[-1] == 'member'
        fields = self.list_display if is_list_request else self.fields

        return queryset.select_related('user') \
            .only(*fields)

    @admin.display(description='User is active?', boolean=True)
    def user__is_active(self, obj):
        if obj.user:
            return obj.user.is_active
        return False

    def has_view_permission(self, request, obj=None):
        # allow for all
        return True

    def has_module_permission(self, request):
        return True

    def has_add_permission(self, request):
        # only syncing from contract
        return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        if not obj:
            return False

        if (request.user == obj.user
                and request.user.is_active
                and request.user.is_staff):
            return True

        return False

    def has_delete_permission(self, request, obj=None):
        # only syncing from contract
        return False
