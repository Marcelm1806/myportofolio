import uuid

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0003_experience_organization_experience_role_timeline_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Education",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("institution", models.CharField(max_length=255)),
                ("degree", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("start_year", models.PositiveIntegerField(validators=[
                    django.core.validators.MinValueValidator(1900),
                    django.core.validators.MaxValueValidator(2100),
                ])),
                ("end_year", models.PositiveIntegerField(blank=True, null=True, validators=[
                    django.core.validators.MinValueValidator(1900),
                    django.core.validators.MaxValueValidator(2100),
                ])),
                ("is_current", models.BooleanField(default=False)),
                ("website", models.URLField(blank=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name_plural": "education entries",
                "ordering": ["display_order", "-start_year", "institution", "id"],
            },
        ),
    ]
