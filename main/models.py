import uuid

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