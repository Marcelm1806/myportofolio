from django import forms

from main.models import Education, Project


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


class EducationForm(forms.ModelForm):
    """All editable education fields; Django supplies UUID and timestamps."""

    class Meta:
        model = Education
        fields = [
            "institution",
            "degree",
            "description",
            "start_year",
            "end_year",
            "is_current",
            "website",
            "display_order",
        ]
        labels = {
            "degree": "Degree / programme",
            "is_current": "Currently studying",
            "website": "Institution website",
        }
        help_texts = {
            "description": "Optional faculty, focus, or programme details.",
            "start_year": "Enter a year from 1900 to 2100.",
            "end_year": "Required for completed studies; leave empty if currently studying.",
            "is_current": "Select this for an ongoing degree or exchange semester.",
            "website": "Optional full URL, for example https://www.example.edu/.",
            "display_order": "Use 0 or a higher number. Lower numbers appear first.",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "start_year": forms.NumberInput(attrs={"min": 1900, "max": 2100, "step": 1}),
            "end_year": forms.NumberInput(attrs={"min": 1900, "max": 2100, "step": 1}),
            "display_order": forms.NumberInput(attrs={"min": 0, "step": 1}),
        }
