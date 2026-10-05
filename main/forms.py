from django import forms
from django.utils.html import strip_tags

from main.models import Education, Project


class ProjectForm(forms.ModelForm):
    """Create projects using the portfolio's existing model fields."""

    def clean(self):
        cleaned_data = super().clean()
        # Both the regular form and the AJAX endpoint store plain text.
        # Output escaping is still necessary for existing or imported records.
        for name in (
            "title", "organization", "context_label", "summary",
            "contribution", "technologies", "award",
        ):
            if name not in cleaned_data:
                continue
            value = strip_tags(cleaned_data[name]).strip()
            if self.fields[name].required and not value:
                self.add_error(name, "Enter text, not just HTML tags.")
            else:
                cleaned_data[name] = value
        return cleaned_data

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

    def clean_institution(self):
        institution = strip_tags(self.cleaned_data["institution"]).strip()
        if not institution:
            raise forms.ValidationError("Enter an institution name, not just HTML tags.")
        return institution

    def clean_degree(self):
        degree = strip_tags(self.cleaned_data["degree"]).strip()
        if not degree:
            raise forms.ValidationError("Enter a degree or programme, not just HTML tags.")
        return degree

    def clean_description(self):
        # Plain text only. Rendering must still escape old/imported values.
        return strip_tags(self.cleaned_data["description"]).strip()

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
