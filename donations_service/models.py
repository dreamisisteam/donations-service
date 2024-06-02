from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

from django_resized import ResizedImageField

from donations_service import querysets


class Member(models.Model):
    """Member model"""

    address = models.CharField(
        unique=True,
        editable=False,
        null=False,
        max_length=42,
        db_index=True,
    )
    needs = models.JSONField(
        null=True,
        blank=True,
    )
    charges = models.PositiveBigIntegerField(
        null=True,
    )
    total = models.PositiveBigIntegerField(
        null=True,
    )

    description = models.TextField(
        max_length=1000,
        null=True,
        blank=True,
    )
    tags = ArrayField(
        models.CharField(max_length=64),
        default=list,
        max_length=4,
        blank=True,
    )
    avatar = ResizedImageField(
        size=[300, 300],
        crop=["middle", "center"],
        upload_to="avatars",
        null=True,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member",
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = querysets.MembersQuerySet.as_manager()

    @property
    def is_active(self):
        """Shows if user is active"""
        if not (user_id := self.user_id):
            return False

        return get_user_model().objects.only("is_active").get(id=user_id).is_active

    @property
    def avatar_url(self):
        """Represents the image url"""
        return self.avatar.url if self.avatar else None

    class Meta:
        ordering = (
            "-updated_at",
            "created_at",
        )
