"""Tutorial 5: AJAX contracts, authorization, CSRF, filtering and plain text."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from main.forms import ProjectForm
from main.models import Project
from main.tests_tutorial3 import project_data
from main.views import get_projects_json


class ProjectAjaxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        accounts = get_user_model().objects
        cls.owner = accounts.create_user(username="ajax-owner", is_superuser=True, is_staff=True)
        cls.member = accounts.create_user(username="ajax-member", email="private@example.test")
        cls.staff = accounts.create_user(username="ajax-staff", is_staff=True)
        cls.editor = accounts.create_user(username="ajax-editor")
        cls.editor.groups.add(Group.objects.get_or_create(name="Editor")[0])
        cls.existing = Project.objects.create(**project_data())
        cls.existing.starred_by.add(cls.member)

    def test_list_renders_shell_without_querying_projects_or_deserializing(self):
        with self.assertNumQueries(0):
            response = self.client.get(reverse("main:show_projects"), {"title": "  Analytics  "})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.existing.title)
        self.assertContains(response, 'id="project-grid"')
        self.assertContains(response, "Loading projects")
        self.assertContains(response, "js/projects.js")
        self.assertEqual(response.context["project_config"]["initialQuery"], "Analytics")
        self.assertIn("csrftoken", response.cookies)
        self.assertNotIn("project_list", response.context)

    def test_owner_popover_has_all_editable_fields_and_csrf(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("main:show_projects"))
        self.assertTemplateUsed(response, "components/project_form_modal.html")
        self.assertContains(response, 'id="project-form"')
        self.assertContains(response, 'popover="auto"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        for name in ProjectForm.Meta.fields:
            self.assertContains(response, f'name="{name}"')

    def test_search_value_is_escaped_in_input_and_json_configuration(self):
        payload = '</script><img src=x onerror="alert(1)">'
        response = self.client.get(reverse("main:show_projects"), {"title": payload})
        self.assertNotContains(response, payload)
        self.assertContains(response, "\\u003C/script\\u003E")
        self.assertEqual(response.context["project_config"]["initialQuery"], payload)

    def test_json_contains_current_session_star_state_and_no_account_secrets(self):
        for account, expected in ((None, False), (self.member, True), (self.owner, False)):
            with self.subTest(account=account):
                self.client.logout()
                if account:
                    self.client.force_login(account)
                response = self.client.get(reverse("main:get_projects_json"))
                fields = response.json()[0]["fields"]
                self.assertEqual(fields["is_starred"], expected)
                self.assertEqual(fields["star_count"], 1)
                self.assertEqual(fields["starred_by_names"], "ajax-member")
                self.assertIn("Cookie", response["Vary"])
                self.assertNotContains(response, "private@example.test")
                self.assertNotContains(response, "password")
                self.assertNotContains(response, "is_superuser")

    def test_json_prefetch_has_constant_query_cost(self):
        for index in range(4):
            project = Project.objects.create(**{**project_data(), "title": f"Project {index}"})
            project.starred_by.add(self.member, self.editor)
        request = RequestFactory().get(reverse("main:get_projects_json"))
        request.user = AnonymousUser()
        with self.assertNumQueries(2):
            response = get_projects_json(request)
        self.assertEqual(response.status_code, 200)

    def test_ajax_create_returns_201_and_preserves_existing_data_and_stars(self):
        self.client.force_login(self.owner)
        data = {**project_data(), "title": "New AJAX Project", "is_featured": "on", "starred_by": [self.member.pk]}
        response = self.client.post(reverse("main:create_project_ajax"), data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["message"], "Project added successfully.")
        created = Project.objects.get(pk=response.json()["pk"])
        self.assertEqual(created.title, data["title"])
        self.assertTrue(created.is_featured)
        self.assertEqual(created.starred_by.count(), 0)
        self.assertEqual(Project.objects.count(), 2)
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.summary, project_data()["summary"])
        self.assertEqual(list(self.existing.starred_by.all()), [self.member])
        records = self.client.get(reverse("main:get_projects_json"), {"title": " new ajax "}).json()
        self.assertEqual([record["pk"] for record in records], [str(created.pk)])

    def test_unauthorized_ajax_create_is_json_403_not_a_login_redirect(self):
        for account in (None, self.member, self.staff, self.editor):
            with self.subTest(account=account):
                self.client.logout()
                if account:
                    self.client.force_login(account)
                response = self.client.post(reverse("main:create_project_ajax"), project_data())
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response["Content-Type"], "application/json")
                self.assertIn("message", response.json())
                self.assertNotIn("Location", response)
        self.assertEqual(Project.objects.count(), 1)

    def test_ajax_create_only_accepts_post(self):
        self.client.force_login(self.owner)
        url = reverse("main:create_project_ajax")
        for method in (self.client.get, self.client.head, self.client.put, self.client.delete):
            self.assertEqual(method(url).status_code, 405)
        self.assertEqual(Project.objects.count(), 1)

    def test_ajax_validates_required_length_and_numeric_fields(self):
        self.client.force_login(self.owner)
        cases = [({}, "title"),
                 ({**project_data(), "title": "x" * 256}, "title"),
                 ({**project_data(), "display_order": "-1"}, "display_order"),
                 ({**project_data(), "display_order": "abc"}, "display_order")]
        for data, field in cases:
            with self.subTest(field=field):
                response = self.client.post(reverse("main:create_project_ajax"), data)
                self.assertEqual(response.status_code, 400)
                self.assertIn("message", response.json()["errors"][field][0])
                self.assertIn("code", response.json()["errors"][field][0])
                self.assertEqual(Project.objects.count(), 1)

    def test_ajax_csrf_header_is_required_even_for_the_owner(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        page = client.get(reverse("main:show_projects"))
        url = reverse("main:create_project_ajax")
        self.assertEqual(client.post(url, project_data()).status_code, 403)
        self.assertEqual(client.post(url, project_data(), HTTP_X_CSRFTOKEN="invalid").status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        response = client.post(url, project_data(), HTTP_X_CSRFTOKEN=page.context["project_config"]["csrfToken"])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Project.objects.count(), 2)

    def test_guest_with_valid_csrf_still_cannot_create(self):
        client = Client(enforce_csrf_checks=True)
        page = client.get(reverse("main:show_projects"))
        response = client.post(reverse("main:create_project_ajax"), project_data(), HTTP_X_CSRFTOKEN=page.context["project_config"]["csrfToken"])
        self.assertEqual(response.status_code, 403)
        self.assertIn("message", response.json())
        self.assertEqual(Project.objects.count(), 1)

    def test_regular_and_ajax_forms_both_strip_markup_from_all_text_fields(self):
        self.client.force_login(self.owner)
        data = {**project_data(), "title": ' <img src=x onerror="alert(1)">Safe title ',
                "organization": "<b>University</b>", "context_label": "<i>Context</i>",
                "summary": "<script>alert(1)</script>Summary", "contribution": "<em>Work</em>",
                "technologies": "<b>Python</b>\nSQL", "award": "<strong>Award</strong>"}
        for name, code in (("main:create_project", 302), ("main:create_project_ajax", 201)):
            response = self.client.post(reverse(name), data)
            self.assertEqual(response.status_code, code)
        for project in Project.objects.exclude(pk=self.existing.pk):
            self.assertEqual(project.title, "Safe title")
            self.assertEqual(project.summary, "alert(1)Summary")
            self.assertEqual(project.organization, "University")
            self.assertEqual(project.technology_list, ["Python", "SQL"])
            self.assertEqual(project.contribution, "Work")
            self.assertEqual(project.award, "Award")

    def test_required_fields_cannot_become_empty_after_stripping_tags(self):
        self.client.force_login(self.owner)
        for field in ("title", "organization", "summary", "contribution"):
            response = self.client.post(reverse("main:create_project_ajax"), {
                **project_data(), field: ' <img src=x onerror="alert(1)"> ',
            })
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.json()["errors"])
        self.assertEqual(Project.objects.count(), 1)
