from django import forms

from main.models import Project


class ProjectForm(forms.ModelForm):
    """Create projects using the portfolio's existing model fields."""

    class Meta:
        model = Project
        fields = [
            "title",
            "organization",
            "context_label",
            "summary",
            "contribution",
            "technologies",
            "award",
            "is_featured",
            "display_order",
        ]
        labels = {
            "organization": "Organization / university",
            "context_label": "Project context",
            "contribution": "My contribution",
            "technologies": "Technologies & topics",
            "is_featured": "Feature this project",
        }
        help_texts = {
            "context_label": "Optional, for example: University project.",
            "award": "Optional award name, without the word 'Award'.",
            "is_featured": "Featured projects appear first as a wide, dark card.",
            "display_order": "Use 0 or a higher number. Lower numbers appear first within each featured group.",
        }
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "contribution": forms.Textarea(attrs={"rows": 5}),
            "technologies": forms.Textarea(attrs={"rows": 3}),
            "display_order": forms.NumberInput(attrs={"min": 0, "step": 1}),
        }
