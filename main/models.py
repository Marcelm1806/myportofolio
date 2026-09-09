import uuid

from django.db import models

# Create your models here.


class Experience(models.Model):
    EXPERIENCE_CHOICES = [
        ("internship", "Internship"),
        ("research", "Research"),
        ("volunteer", "Volunteer"),
        ("part-time", "Part-Time"),
        ("full-time", "Full-Time"),
        ("freelance", "Freelance"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        default="full-time",
    )
    thumbnail = models.URLField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    @property
    def is_ongoing(self):
        return self.ended_at is None

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