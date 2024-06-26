# Generated by Django 4.2.6 on 2024-06-02 22:24

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django_resized.forms


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Member",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "address",
                    models.CharField(
                        db_index=True, editable=False, max_length=42, unique=True
                    ),
                ),
                ("needs", models.JSONField(blank=True, null=True)),
                ("charges", models.PositiveBigIntegerField(null=True)),
                ("total", models.PositiveBigIntegerField(null=True)),
                (
                    "description",
                    models.TextField(blank=True, max_length=1000, null=True),
                ),
                (
                    "tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=64),
                        blank=True,
                        default=list,
                        max_length=4,
                        size=None,
                    ),
                ),
                (
                    "avatar",
                    django_resized.forms.ResizedImageField(
                        crop=["middle", "center"],
                        force_format="JPEG",
                        keep_meta=True,
                        null=True,
                        quality=-1,
                        scale=None,
                        size=[300, 300],
                        upload_to="avatars",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="member",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-updated_at", "created_at"),
            },
        ),
    ]
