import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Experience(models.Model):
    """A professional experience with its period and responsibilities."""

    EXPERIENCE_CHOICES = [
        ("internship", "Internship"),
        ("research", "Research"),
        ("volunteer", "Volunteer"),
        ("part-time", "Part-Time"),
        ("full-time", "Full-Time"),
        ("freelance", "Freelance"),
        ("intern-working", "Intern & Working Student"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    role_timeline = models.CharField(max_length=255, blank=True)
    category = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        default="full-time",
    )
    thumbnail = models.URLField(blank=True, null=True)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    @property
    def is_ongoing(self):
        return self.ended_at is None

    @property
    def responsibility_list(self):
        """Return one responsibility per non-empty description line."""
        return [
            line.strip()
            for line in self.description.splitlines()
            if line.strip()
        ]


class Project(models.Model):
    """A portfolio project with content for its list and detail pages."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    context_label = models.CharField(max_length=255, blank=True)
    summary = models.TextField()
    contribution = models.TextField()
    technologies = models.TextField(
        blank=True,
        help_text="Enter one technology or topic per line.",
    )
    award = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    starred_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="starred_projects",
        blank=True,
    )

    class Meta:
        ordering = ["-is_featured", "display_order", "title"]

    def __str__(self):
        return self.title

    @property
    def technology_list(self):
        """Return non-empty technology names for display as tags."""
        return [
            line.strip()
            for line in self.technologies.splitlines()
            if line.strip()
        ]


class Education(models.Model):
    """An academic entry; use years because exact study dates are not known."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
    )
    end_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
    )
    is_current = models.BooleanField(default=False)
    website = models.URLField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "-start_year", "institution", "id"]
        verbose_name_plural = "education entries"

    def __str__(self):
        return f"{self.degree} — {self.institution}"

    def clean(self):
        """ModelForm calls this validation on both create and update."""
        super().clean()
        if self.is_current and self.end_year is not None:
            raise ValidationError({
                "end_year": "Leave the end year empty while currently studying.",
            })
        if not self.is_current and self.end_year is None:
            raise ValidationError({
                "end_year": "Enter an end year or select Currently studying.",
            })
        if (
            self.start_year is not None
            and self.end_year is not None
            and self.end_year < self.start_year
        ):
            raise ValidationError({
                "end_year": "The end year cannot be earlier than the start year.",
            })

    @property
    def period_label(self):
        if self.is_current:
            return f"{self.start_year}–Present"
        if self.end_year == self.start_year:
            return str(self.start_year)
        return f"{self.start_year}–{self.end_year}"
