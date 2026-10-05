"""Education CRUD, JSON delivery, and integration with the existing portfolio."""

import io
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from main.forms import EducationForm
from main.models import Education, Experience, Project


def education_data(**changes):
    data = {
        "institution": "Example University",
        "degree": "B.Sc. Information Systems",
        "description": "Data analysis and information systems.",
        "start_year": "2020",
        "end_year": "2025",
        "website": "https://example.edu/",
        "display_order": "2",
    }
    return {**data, **changes}


class EducationWriteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(
            username="education-test-owner", is_superuser=True, is_staff=True,
        )
        cls.existing = Education.objects.create(
            institution="Existing University", degree="Existing degree",
            start_year=2018, end_year=2021,
        )
        cls.other = Education.objects.create(
            institution="Other University", degree="Other degree",
            start_year=2024, is_current=True,
        )

    def setUp(self):
        self.client.force_login(self.owner)

    def test_create_form_has_editable_fields_and_no_generated_inputs(self):
        response = self.client.get(reverse("main:create_education"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], EducationForm)
        self.assertFalse(response.context["form"].is_bound)
        self.assertTemplateUsed(response, "components/form_fields.html")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        for field in ("institution", "degree", "description", "start_year",
                      "end_year", "is_current", "website", "display_order"):
            self.assertContains(response, f'name="{field}"')
        for field in ("id", "created_at", "updated_at"):
            self.assertNotContains(response, f'name="{field}"')
        self.assertContains(response, 'type="checkbox"')
        self.assertContains(response, 'type="number"')
        self.assertContains(response, 'type="url"')

    def test_create_redirects_and_refresh_does_not_duplicate(self):
        response = self.client.post(
            reverse("main:create_education"), education_data(), follow=True,
        )
        self.assertRedirects(response, reverse("main:show_education"))
        self.assertContains(response, "Education entry added successfully.")
        entry = Education.objects.get(institution="Example University")
        self.assertIsInstance(entry.pk, uuid.UUID)
        self.assertEqual(entry.start_year, 2020)
        self.assertFalse(entry.is_current)
        self.assertIsNotNone(entry.created_at)
        self.assertIsNotNone(entry.updated_at)
        self.assertEqual(Education.objects.count(), 3)
        self.client.get(reverse("main:show_education"))
        self.assertEqual(Education.objects.count(), 3)
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.institution, "Existing University")

    def test_edit_get_prefills_the_selected_record_without_saving(self):
        response = self.client.get(reverse("main:update_education", args=[self.existing.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].instance.pk, self.existing.pk)
        self.assertContains(response, 'value="Existing University"')
        self.assertContains(response, 'value="2018"')
        self.assertContains(response, "Save changes")
        self.assertEqual(Education.objects.count(), 2)

    def test_update_preserves_identity_and_creation_time_without_inserting(self):
        created_at = self.existing.created_at
        updated_at = self.existing.updated_at
        response = self.client.post(
            reverse("main:update_education", args=[self.existing.pk]),
            education_data(institution="Updated University", end_year="", is_current="on"),
            follow=True,
        )
        self.assertRedirects(response, reverse("main:show_education"))
        self.assertContains(response, "Education entry updated successfully.")
        self.assertEqual(Education.objects.count(), 2)
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.institution, "Updated University")
        self.assertTrue(self.existing.is_current)
        self.assertIsNone(self.existing.end_year)
        self.assertEqual(self.existing.created_at, created_at)
        self.assertGreaterEqual(self.existing.updated_at, updated_at)
        self.other.refresh_from_db()
        self.assertEqual(self.other.institution, "Other University")

    def test_invalid_create_shows_errors_and_keeps_values_without_saving(self):
        cases = [
            ({}, "institution"),
            (education_data(institution="   "), "institution"),
            (education_data(degree="x" * 256), "degree"),
            (education_data(start_year="not-a-year"), "start_year"),
            (education_data(start_year="1899"), "start_year"),
            (education_data(end_year="2101"), "end_year"),
            (education_data(end_year="2019"), "end_year"),
            (education_data(end_year=""), "end_year"),
            (education_data(is_current="on"), "end_year"),
            (education_data(display_order="-1"), "display_order"),
            (education_data(website="javascript:alert(1)"), "website"),
        ]
        for data, field in cases:
            with self.subTest(field=field, data=data):
                response = self.client.post(reverse("main:create_education"), data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].is_bound)
                self.assertIn(field, response.context["form"].errors)
                self.assertContains(response, "Please correct the highlighted fields")
                self.assertEqual(Education.objects.count(), 2)
                if data.get("institution") == "Example University":
                    self.assertContains(response, 'value="Example University"')

    def test_invalid_update_does_not_change_the_database(self):
        response = self.client.post(
            reverse("main:update_education", args=[self.existing.pk]),
            education_data(end_year="2019"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("end_year", response.context["form"].errors)
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.institution, "Existing University")
        self.assertEqual(self.existing.end_year, 2021)
        self.assertEqual(Education.objects.count(), 2)

    def test_submitted_ids_and_timestamps_cannot_overwrite_another_record(self):
        data = education_data(
            id=str(self.other.pk), created_at="2000-01-01T00:00:00Z",
            updated_at="2000-01-01T00:00:00Z",
        )
        self.assertEqual(self.client.post(reverse("main:create_education"), data).status_code, 302)
        entry = Education.objects.get(institution="Example University")
        self.assertNotEqual(entry.pk, self.other.pk)
        self.assertNotEqual(entry.created_at.year, 2000)
        response = self.client.post(
            reverse("main:update_education", args=[self.existing.pk]), data,
        )
        self.assertEqual(response.status_code, 302)
        self.other.refresh_from_db()
        self.assertEqual(self.other.institution, "Other University")
        self.assertEqual(Education.objects.count(), 3)

    def test_unsupported_methods_cannot_modify_or_delete_entries(self):
        delete_url = reverse("main:delete_education", args=[self.existing.pk])
        for method in (self.client.get, self.client.head, self.client.delete):
            self.assertEqual(method(delete_url).status_code, 405)
        for url in (reverse("main:create_education"),
                    reverse("main:update_education", args=[self.existing.pk])):
            self.assertEqual(self.client.put(url).status_code, 405)
        self.assertEqual(Education.objects.count(), 2)

    def test_delete_removes_only_selected_entry_and_redirects(self):
        response = self.client.post(
            reverse("main:delete_education", args=[self.existing.pk]), follow=True,
        )
        self.assertRedirects(response, reverse("main:show_education"))
        self.assertContains(response, "Education entry deleted successfully.")
        self.assertFalse(Education.objects.filter(pk=self.existing.pk).exists())
        self.assertTrue(Education.objects.filter(pk=self.other.pk).exists())

    def test_missing_and_malformed_ids_return_404(self):
        missing = uuid.uuid4()
        for method in (self.client.get, self.client.post):
            self.assertEqual(method(reverse("main:update_education", args=[missing])).status_code, 404)
        self.assertEqual(self.client.post(reverse("main:delete_education", args=[missing])).status_code, 404)
        self.assertEqual(self.client.get("/education/not-a-uuid/edit/").status_code, 404)
        self.assertEqual(Education.objects.count(), 2)

    def test_create_update_and_delete_require_csrf_tokens(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        urls = (
            reverse("main:create_education"),
            reverse("main:update_education", args=[self.existing.pk]),
            reverse("main:delete_education", args=[self.existing.pk]),
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(client.post(url, education_data()).status_code, 403)
        self.assertEqual(Education.objects.count(), 2)
        client.get(urls[0])
        token = client.cookies["csrftoken"].value
        for url in urls:
            with self.subTest(valid_csrf=url):
                response = client.post(url, {**education_data(), "csrfmiddlewaretoken": token})
                self.assertEqual(response.status_code, 302)
        self.assertEqual(Education.objects.count(), 2)
        self.assertFalse(Education.objects.filter(pk=self.existing.pk).exists())


class EducationDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(
            username="education-layout-owner", is_superuser=True, is_staff=True,
        )
        cls.current = Education.objects.create(
            institution="Current University", degree="M.Sc. Data Science",
            description="Research & practical work", start_year=2024,
            is_current=True, display_order=0,
        )
        cls.completed = Education.objects.create(
            institution="Earlier University", degree="B.Sc. Information Systems",
            start_year=2020, end_year=2023, display_order=1,
        )

    def test_json_serializes_types_ids_timestamps_and_order(self):
        response = self.client.get(reverse("main:get_education_json"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        records = response.json()
        self.assertEqual([r["pk"] for r in records], [str(self.current.pk), str(self.completed.pk)])
        self.assertEqual(records[0]["model"], "main.education")
        self.assertIs(records[0]["fields"]["is_current"], True)
        self.assertEqual(records[0]["fields"]["start_year"], 2024)
        self.assertIsNone(records[0]["fields"]["end_year"])
        self.assertIn("created_at", records[0]["fields"])
        self.assertIn("updated_at", records[0]["fields"])
        self.assertEqual(records[0]["fields"]["period_label"], "2024–Present")
        self.assertEqual(records[1]["fields"]["period_label"], "2020–2023")

    def test_page_renders_a_shell_without_loading_the_json_server_side(self):
        # Assignment 5 replaces the earlier server-side serializer round trip.
        with patch("main.views.get_education_json") as endpoint:
            with self.assertNumQueries(0):
                response = self.client.get(reverse("main:show_education"))
        endpoint.assert_not_called()
        self.assertContains(response, 'id="education-grid"')
        self.assertContains(response, "js/education.js")
        self.assertNotContains(response, self.current.institution)
        self.assertNotIn("education_list", response.context)

    def test_search_and_status_filters_match_in_html_and_json(self):
        cases = [
            ({"q": "  cUrReNt  "}, [self.current]),
            ({"q": "information"}, [self.completed]),
            ({"status": "current"}, [self.current]),
            ({"status": "completed"}, [self.completed]),
            ({"q": "university", "status": "current"}, [self.current]),
            ({"q": "Current", "status": "completed"}, []),
            ({"q": "   ", "status": "unknown"}, [self.current, self.completed]),
        ]
        for query, entries in cases:
            with self.subTest(query=query):
                html = self.client.get(reverse("main:show_education"), query)
                data = self.client.get(reverse("main:get_education_json"), query).json()
                self.assertEqual(html.context["education_config"]["initialFilters"]["q"], query.get("q", "").strip())
                self.assertEqual([e["pk"] for e in data], [str(e.pk) for e in entries])
        self.assertEqual(Education.objects.count(), 2)

    def test_empty_state_differs_from_no_matching_results(self):
        response = self.client.get(reverse("main:show_education"), {"q": "Missing"})
        self.assertContains(response, "No education entries match these filters.")
        Education.objects.all().delete()
        response = self.client.get(reverse("main:show_education"))
        self.assertContains(response, "No education entries have been added yet.")
        self.assertEqual(self.client.get(reverse("main:get_education_json")).json(), [])

    def test_home_shows_current_database_content_without_search_filters(self):
        self.current.institution = "Renamed University"
        self.current.save()
        response = self.client.get(reverse("main:show_main"), {"q": "Missing", "status": "completed"})
        self.assertContains(response, "Renamed University")
        self.assertContains(response, self.completed.institution)
        self.assertContains(response, 'id="education"')
        self.assertContains(response, f'href="{reverse("main:show_education")}"')
        self.current.delete()
        response = self.client.get(reverse("main:show_main"))
        self.assertNotContains(response, "Renamed University")

    def test_user_content_is_escaped_and_controls_target_each_record(self):
        self.client.force_login(self.owner)
        self.current.institution = '<script>alert("test")</script>'
        self.current.description = '<img src=x onerror="alert(1)">'
        self.current.save()
        response = self.client.get(reverse("main:show_education_detail", args=[self.current.pk]))
        self.assertNotContains(response, self.current.institution)
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<img src=x')
        self.assertContains(response, f'popovertarget="delete-education-{self.current.pk}"')
        self.assertContains(response, f'action="{reverse("main:delete_education", args=[self.current.pk])}"')
        self.assertContains(response, f'href="{reverse("main:update_education", args=[self.current.pk])}"')

    def test_read_endpoints_reject_posts(self):
        for name in ("main:get_education_json", "main:show_education",
                     "main:get_experience_json", "main:show_experience", "main:show_main"):
            with self.subTest(name=name):
                self.assertEqual(self.client.post(reverse(name)).status_code, 405)
        self.assertEqual(Education.objects.count(), 2)

    def test_full_pages_share_one_base_layout_and_education_navigation(self):
        self.client.force_login(self.owner)
        project = Project.objects.create(
            title="Test project", organization="Example",
            summary="Summary", contribution="Contribution",
        )
        urls = [reverse(name) for name in (
            "main:show_main", "main:show_projects", "main:create_project",
            "main:show_experience", "main:show_education", "main:create_education",
        )]
        urls += [reverse("main:show_project_detail", args=[project.pk]),
                 reverse("main:update_education", args=[self.current.pk])]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "base.html")
                self.assertContains(response, "<!DOCTYPE html>", count=1)
                self.assertContains(response, '<main id="main-content"', count=1)
                self.assertContains(response, f'href="{reverse("main:show_education")}"')

    def test_experience_json_and_page_preserve_model_properties(self):
        experience = Experience.objects.create(
            title="Data analyst", description="First task\nSecond task",
            organization="Example Company", ended_at=timezone.now(),
        )
        response = self.client.get(reverse("main:get_experience_json"))
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()[0]["pk"], str(experience.pk))
        self.assertEqual(response.json()[0]["model"], "main.experience")
        html = self.client.get(reverse("main:show_experience"))
        self.assertContains(html, "First task")
        self.assertContains(html, "Second task")
        self.assertContains(html, "Completed")
        self.assertFalse(html.context["experience_list"][0].is_ongoing)


class EducationFixtureTests(TestCase):
    def test_fixture_loads_three_entries_and_preserves_independent_records(self):
        own = Education.objects.create(
            institution="Independent Institute", degree="Certificate",
            start_year=2025, end_year=2025,
        )
        for _ in range(2):
            call_command("loaddata", "main/education.json", stdout=io.StringIO())
        self.assertEqual(Education.objects.count(), 4)
        self.assertTrue(Education.objects.filter(pk=own.pk).exists())
        for entry in Education.objects.all():
            entry.full_clean()
        self.assertEqual(Education.objects.get(institution="University of Mannheim").period_label, "2020–2025")
        self.assertTrue(Education.objects.get(institution="Universitas Indonesia").is_current)

    def test_period_labels_cover_current_completed_and_single_year_study(self):
        cases = [
            ({"start_year": 2024, "is_current": True}, "2024–Present"),
            ({"start_year": 2020, "end_year": 2025}, "2020–2025"),
            ({"start_year": 2026, "end_year": 2026}, "2026"),
        ]
        for values, label in cases:
            with self.subTest(values=values):
                entry = Education(institution="Example", degree="Course", **values)
                self.assertEqual(entry.period_label, label)
                self.assertEqual(str(entry), "Course — Example")
