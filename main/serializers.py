"""Versioned, flat REST representations of the existing portfolio models."""

from collections.abc import Mapping

from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from django.utils.html import strip_tags
from rest_framework import serializers

from main.models import Education, Project


class PlainTextModelSerializer(serializers.ModelSerializer):
    """Apply the forms' plain-text policy before DRF's field validation."""

    plain_text_fields = ()

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            data = data.copy()
            for name in self.plain_text_fields:
                if isinstance(data.get(name), str):
                    data[name] = strip_tags(data[name]).strip()
        # Required, length, numeric and URL validation still belong to DRF.
        return super().to_internal_value(data)


class ProjectSerializer(PlainTextModelSerializer):
    plain_text_fields = (
        "title", "organization", "context_label", "summary", "contribution",
        "technologies", "award",
    )
    technology_list = serializers.ReadOnlyField()
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()
    urls = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id", "title", "organization", "context_label", "summary",
            "contribution", "technologies", "award", "is_featured",
            "display_order", "technology_list", "star_count", "is_starred",
            "starred_by_names", "urls",
        )
        read_only_fields = ("id",)

    def get_star_count(self, obj):
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and any(
            user.pk == request.user.pk for user in obj.starred_by.all()
        ))

    def get_starred_by_names(self, obj):
        # Tutorial 5 already exposes usernames, never emails or credentials.
        return ", ".join(user.get_username() for user in obj.starred_by.all())

    def get_urls(self, obj):
        return {
            "detail": reverse("main:show_project_detail", args=[obj.pk]),
            "api_detail": reverse("api:project_detail", args=[obj.pk]),
            "star": reverse("api:toggle_project_star", args=[obj.pk]),
        }


class EducationSerializer(serializers.ModelSerializer):
    period_label = serializers.ReadOnlyField()
    star_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    urls = serializers.SerializerMethodField()

    class Meta:
        model = Education
        fields = (
            "id", "institution", "degree", "description", "start_year",
            "end_year", "is_current", "website", "display_order",
            "created_at", "updated_at", "period_label", "star_count",
            "is_starred", "urls",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    @staticmethod
    def _required_text(value, message):
        text = strip_tags(value).strip()
        if not text:
            raise serializers.ValidationError(message)
        return text

    def validate_institution(self, value):
        return self._required_text(value, "Enter an institution name, not just HTML tags.")

    def validate_degree(self, value):
        return self._required_text(value, "Enter a degree or programme, not just HTML tags.")

    def validate_description(self, value):
        return strip_tags(value).strip()

    def validate(self, attrs):
        # ModelSerializer does not call Model.clean(). Merge existing values so
        # PATCH also checks relationships between changed and unchanged fields.
        names = (
            "institution", "degree", "description", "start_year", "end_year",
            "is_current", "website", "display_order",
        )
        values = {name: getattr(self.instance, name) for name in names} if self.instance else {}
        candidate = Education(**{**values, **attrs})
        try:
            candidate.clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        return attrs

    def get_star_count(self, obj):
        # List/detail querysets annotate this in one query; a fresh create does not.
        if hasattr(obj, "star_count"):
            return obj.star_count
        return obj.starred_by.count()

    def get_is_starred(self, obj):
        if hasattr(obj, "is_starred"):
            return obj.is_starred
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and
                    obj.starred_by.filter(pk=request.user.pk).exists())

    def get_urls(self, obj):
        return {
            "detail": reverse("main:show_education_detail", args=[obj.pk]),
            "edit": reverse("main:update_education", args=[obj.pk]),
            "api_detail": reverse("api:education_detail", args=[obj.pk]),
            "star": reverse("api:toggle_education_star", args=[obj.pk]),
        }
