from django.contrib import admin

from donations_service import models


class MemberIsActiveFilter(admin.SimpleListFilter):
    """Filter of members active state"""

    title = "Is active?"
    parameter_name = "is_active"

    def lookups(self, request, model_admin):
        """Lookups of choices"""
        return (
            (1, "Yes"),
            (0, "No"),
        )

    def queryset(self, request, queryset):
        """Get queryset for filter"""
        if not (value := self.value()):
            return queryset

        filter_function = "filter" if bool(int(value)) else "exclude"
        return getattr(queryset, filter_function)(user__is_active=True)


@admin.register(models.Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin representation of Member model"""

    fields = (
        "description",
        "tags",
        "avatar",
        "address",
        "needs",
        "charges",
        "total",
        "user",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "address",
        "needs",
        "charges",
        "total",
        "user",
        "created_at",
        "updated_at",
    )

    list_display = (
        "address",
        "user__username",
        "user__is_active",
        "created_at",
        "updated_at",
    )
    list_filter = (MemberIsActiveFilter,)

    search_fields = (
        "address",
        "user__username",
    )

    def get_queryset(self, request):
        """Get queryset for ModelAdmin"""
        queryset = super().get_queryset(request)

        is_list_request = request.path.strip("/").split("/")[-1] == "member"
        fields = self.list_display if is_list_request else self.fields

        return queryset.select_related("user").only(*fields)

    @admin.display(description="User is active?", boolean=True)
    def user__is_active(self, obj):
        """Get active status of user"""
        if obj.user:
            return obj.user.is_active
        return False

    @admin.display(description="Username")
    def user__username(self, obj):
        """Get username"""
        if obj.user:
            return obj.user.username
        return None

    def has_view_permission(self, request, obj=None):
        """Allow all staff users to view data"""
        return True

    def has_module_permission(self, request):
        """Allow all staff users to view ModelAdmin"""
        return True

    def has_add_permission(self, request):
        """Do not allow add data manually. Syncing from contract"""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow to change obj for admin and obj owner"""
        if request.user.is_superuser:
            return True

        if not obj:
            return False

        if (
            request.user == obj.user and
            request.user.is_active and
            request.user.is_staff
        ):
            return True

        return False

    def has_delete_permission(self, request, obj=None):
        """Do not allow delete data manually"""
        return False
