"""Tutorial 7's API/permission/CSRF checklist, using the real portfolio fields."""

import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from main.models import Education, Project


def project_data(**changes):
    return {
        "title": "Django portfolio", "organization": "University",
        "summary": "A portfolio", "contribution": "Built the application",
        "technologies": "Python\nDjango", "is_featured": False, "display_order": 1,
        **changes,
    }


def education_data(**changes):
    return {
        "institution": "Example University", "degree": "Information Systems",
        "start_year": 2020, "end_year": 2023, "is_current": False, "display_order": 0,
        **changes,
    }


class ApiAccounts(APITestCase):
    @classmethod
    def setUpTestData(cls):
        accounts = get_user_model().objects
        cls.owner = accounts.create_user(username="api-owner", is_superuser=True, is_staff=True)
        cls.member = accounts.create_user(username="api-member", email="private@example.test")
        cls.other = accounts.create_user(username="api-other")
        cls.staff = accounts.create_user(username="api-staff", is_staff=True)
        cls.editor = accounts.create_user(username="api-editor")
        cls.editor.groups.add(Group.objects.create(name="Editor"))
        cls.project = Project.objects.create(**project_data())
        cls.entry = Education.objects.create(**education_data())

    def authenticate(self, user):
        self.client.force_authenticate(user=user)


class ProjectApiTests(ApiAccounts):
    def setUp(self):
        self.list_url = reverse("api:project_list")
        self.detail_url = reverse("api:project_detail", args=[self.project.pk])
        self.star_url = reverse("api:toggle_project_star", args=[self.project.pk])

    def test_01_public_list_and_detail_use_flat_data_and_preserve_featured_order(self):
        featured = Project.objects.create(**project_data(title="Featured", is_featured=True))
        self.project.starred_by.add(self.member)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [str(featured.pk), str(self.project.pk)])
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], self.project.title)
        self.assertNotIn("fields", response.data)
        self.assertNotIn("pk", response.data)
        self.assertEqual(response.data["technology_list"], ["Python", "Django"])
        self.assertEqual(response.data["star_count"], 1)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["starred_by_names"], "api-member")
        self.assertNotIn("private@example.test", str(response.data))
        self.assertIn("Cookie", response["Vary"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(self.client.head(self.detail_url).status_code, 200)

    def test_02_search_is_trimmed_case_insensitive_and_empty_is_200(self):
        self.assertEqual(len(self.client.get(self.list_url, {"title": "  DJANGO  "}).data), 1)
        self.assertEqual(len(self.client.get(self.list_url, {"title": "  "}).data), 1)
        response = self.client.get(self.list_url, {"title": "not found"})
        self.assertEqual((response.status_code, response.data), (200, []))
        self.project.delete()
        self.assertEqual(self.client.get(self.list_url).data, [])

    def test_03_missing_objects_return_json_404(self):
        self.assertEqual(self.client.get(reverse("api:project_detail", args=[uuid.uuid4()])).status_code, 404)
        self.authenticate(self.member)
        response = self.client.post(reverse("api:toggle_project_star", args=[uuid.uuid4()]), {}, format="json")
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.data)

    def test_04_guest_and_member_writes_are_denied_without_changes(self):
        before = list(Project.objects.values())
        for user in (None, self.member):
            self.authenticate(user)
            for method, url, data in (
                ("post", self.list_url, project_data()), ("put", self.detail_url, project_data()),
                ("patch", self.detail_url, {"title": "Forbidden"}), ("delete", self.detail_url, {}),
            ):
                self.assertEqual(getattr(self.client, method)(url, data, format="json").status_code, 403)
        self.assertEqual(list(Project.objects.values()), before)

    def test_05_owner_create_returns_201_and_clean_flat_record(self):
        self.authenticate(self.owner)
        response = self.client.post(self.list_url, project_data(title=" <b>Created</b> "), format="json")
        self.assertEqual(response.status_code, 201)
        saved = Project.objects.get(pk=response.data["id"])
        self.assertEqual(saved.title, "Created")
        self.assertEqual(response.data["star_count"], 0)
        self.assertEqual(self.client.get(response.data["urls"]["api_detail"]).status_code, 200)
        self.assertEqual(Project.objects.count(), 2)

    def test_06_invalid_and_tag_only_values_return_field_errors(self):
        self.authenticate(self.owner)
        for changes, field in (
            ({"title": "   "}, "title"), ({"title": "<img src=x>"}, "title"),
            ({"summary": "<br>"}, "summary"), ({"title": "x" * 256}, "title"),
            ({"display_order": -1}, "display_order"), ({"display_order": "bad"}, "display_order"),
        ):
            response = self.client.post(self.list_url, project_data(**changes), format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.data)
        self.assertEqual(Project.objects.count(), 1)

    def test_07_patch_put_and_delete_have_distinct_contracts(self):
        self.authenticate(self.owner)
        response = self.client.patch(self.detail_url, {"title": "Updated"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"], self.project.summary)
        self.assertEqual(self.client.put(self.detail_url, {"title": "Incomplete"}, format="json").status_code, 400)
        response = self.client.put(self.detail_url, project_data(title="Replaced"), format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Replaced")
        response = self.client.delete(self.detail_url)
        self.assertEqual((response.status_code, response.content), (204, b""))
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_08_star_toggles_only_session_users_membership(self):
        self.project.starred_by.add(self.other)
        self.assertEqual(self.client.post(self.star_url, {}, format="json").status_code, 403)
        self.authenticate(self.member)
        response = self.client.post(self.star_url, {"user_id": self.other.pk}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.data["star_count"], response.data["is_starred"]), (2, True))
        self.assertTrue(self.client.get(self.detail_url).data["is_starred"])
        response = self.client.post(self.star_url, {}, format="json")
        self.assertEqual((response.data["star_count"], response.data["is_starred"]), (1, False))
        self.assertEqual(list(self.project.starred_by.all()), [self.other])

    def test_09_readonly_and_relationship_fields_cannot_be_forged(self):
        self.authenticate(self.owner)
        response = self.client.post(self.list_url, project_data(
            id=str(self.project.pk), starred_by=[self.other.pk], star_count=999,
            is_starred=True, starred_by_names="Forged", urls={"star": "https://evil.test"},
        ), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data["id"], str(self.project.pk))
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["starred_by_names"], "")
        self.assertTrue(response.data["urls"]["star"].startswith("/api/v1/projects/"))
        self.assertEqual(Project.objects.get(pk=response.data["id"]).starred_by.count(), 0)

    def test_10_staff_and_education_editor_cannot_manage_projects(self):
        for user in (self.staff, self.editor):
            self.authenticate(user)
            self.assertEqual(self.client.post(self.list_url, project_data(), format="json").status_code, 403)
            self.assertEqual(self.client.patch(self.detail_url, {"title": "No"}, format="json").status_code, 403)
            self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Django portfolio")

    def test_11_unsupported_methods_return_405_and_options_is_safe(self):
        self.authenticate(self.owner)
        for method, url in (("patch", self.list_url), ("post", self.detail_url), ("get", self.star_url)):
            self.assertEqual(getattr(self.client, method)(url).status_code, 405)
        self.assertEqual(self.client.options(self.list_url).status_code, 200)

    def test_12_real_session_rejects_missing_csrf_for_every_mutation(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.owner)
        for method, url, data in (
            ("post", self.list_url, project_data()), ("put", self.detail_url, project_data()),
            ("patch", self.detail_url, {"title": "No"}), ("delete", self.detail_url, {}),
            ("post", self.star_url, {}),
        ):
            self.assertEqual(getattr(client, method)(url, data, format="json").status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_13_browsable_api_and_real_csrf_protected_create_work(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.owner)
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, 200)
        self.assertIn("text/html", page["Content-Type"])
        self.assertIn("csrftoken", client.cookies)
        response = client.post(self.list_url, project_data(), format="json",
                               HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(client.get("/api-auth/login/").status_code, 200)


class EducationApiTests(ApiAccounts):
    def setUp(self):
        self.list_url = reverse("api:education_list")
        self.detail_url = reverse("api:education_detail", args=[self.entry.pk])
        self.star_url = reverse("api:toggle_education_star", args=[self.entry.pk])

    def test_public_data_and_personal_filter_preserve_totals_and_privacy(self):
        self.entry.starred_by.add(self.member, self.other)
        self.assertEqual(self.client.get(self.list_url, {"starred": "1"}).data, [])
        self.authenticate(self.member)
        response = self.client.get(self.list_url, {"q": " INFORMATION ", "status": "completed", "starred": "1"})
        self.assertEqual(len(response.data), 1)
        item = response.data[0]
        self.assertEqual(item["id"], str(self.entry.pk))
        self.assertEqual((item["star_count"], item["is_starred"]), (2, True))
        self.assertEqual(item["period_label"], "2020–2023")
        self.assertNotIn("starred_by", item)
        self.assertNotIn("starred_by_names", item)
        self.assertNotIn("fields", item)
        self.assertEqual(self.client.get(self.list_url, {"status": "current"}).data, [])

    def test_roles_enforce_guest_member_staff_editor_owner_boundaries(self):
        for user in (None, self.member, self.staff, self.editor):
            self.authenticate(user)
            self.assertEqual(self.client.post(self.list_url, education_data(), format="json").status_code, 403)
            self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
            expected = 200 if user == self.editor else 403
            self.assertEqual(self.client.patch(self.detail_url, {"degree": "Edited"}, format="json").status_code, expected)
        self.authenticate(self.owner)
        created = self.client.post(self.list_url, education_data(), format="json")
        self.assertEqual(created.status_code, 201)
        deleted = self.client.delete(reverse("api:education_detail", args=[created.data["id"]]))
        self.assertEqual((deleted.status_code, deleted.content), (204, b""))

    def test_editor_update_preserves_identity_and_validates_merged_period(self):
        self.authenticate(self.editor)
        for data in ({"start_year": 2024}, {"is_current": True}, {"end_year": None}):
            response = self.client.patch(self.detail_url, data, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("end_year", response.data)
        response = self.client.patch(self.detail_url, {
            "is_current": True, "end_year": None, "institution": " <b>New university</b> ",
            "id": str(uuid.uuid4()), "created_at": "2000-01-01T00:00:00Z",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], str(self.entry.pk))
        self.assertEqual(response.data["institution"], "New university")
        self.assertEqual(response.data["period_label"], "2020–Present")
        self.assertNotEqual(response.data["created_at"], "2000-01-01T00:00:00Z")
        self.assertEqual(self.client.put(self.detail_url, {"degree": "Partial"}, format="json").status_code, 400)
        self.assertEqual(self.client.put(self.detail_url, education_data(), format="json").status_code, 200)

    def test_creation_validates_years_urls_plain_text_and_period(self):
        self.authenticate(self.owner)
        for data, field in (
            ({"start_year": 1899}, "start_year"), ({"end_year": 2101}, "end_year"),
            ({"end_year": 2019}, "end_year"), ({"is_current": True}, "end_year"),
            ({"website": "javascript:alert(1)"}, "website"),
            ({"institution": "<img src=x>"}, "institution"), ({"degree": "  "}, "degree"),
        ):
            response = self.client.post(self.list_url, education_data(**data), format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.data)
        self.assertEqual(Education.objects.count(), 1)

    def test_stars_require_login_ignore_other_identity_and_missing_ids_404(self):
        self.assertEqual(self.client.post(self.star_url).status_code, 403)
        self.entry.starred_by.add(self.other)
        self.authenticate(self.member)
        response = self.client.post(self.star_url, {"user_id": self.other.pk}, format="json")
        self.assertEqual((response.status_code, response.data["star_count"], response.data["is_starred"]), (200, 2, True))
        response = self.client.post(self.star_url)
        self.assertEqual((response.data["star_count"], response.data["is_starred"]), (1, False))
        self.assertEqual(list(self.entry.starred_by.all()), [self.other])
        self.assertEqual(self.client.get(reverse("api:education_detail", args=[uuid.uuid4()])).status_code, 404)
        self.assertEqual(self.client.post(reverse("api:toggle_education_star", args=[uuid.uuid4()])).status_code, 404)

    def test_session_csrf_and_revoked_editor_permissions(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.editor)
        self.assertEqual(client.patch(self.detail_url, {"degree": "No"}, format="json").status_code, 403)
        page = client.get(reverse("main:show_education"))
        token = page.context["education_config"]["csrfToken"]
        self.assertEqual(client.patch(self.detail_url, {"degree": "Allowed"}, format="json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.editor.groups.clear()
        self.assertEqual(client.patch(self.detail_url, {"degree": "Revoked"}, format="json", HTTP_X_CSRFTOKEN=token).status_code, 403)
        self.assertEqual(client.post(self.star_url, {}, format="json", HTTP_X_CSRFTOKEN=token).status_code, 200)

    def test_pages_point_to_versioned_api_and_legacy_routes_remain_available(self):
        for page_name, config_name, api_name in (
            ("main:show_projects", "project_config", "api:project_list"),
            ("main:show_education", "education_config", "api:education_list"),
        ):
            page = self.client.get(reverse(page_name))
            config = page.context[config_name]
            self.assertEqual(config["jsonUrl"], reverse(api_name))
            self.assertEqual(config["createUrl"], reverse(api_name))
            self.assertTrue(config["csrfToken"])
        for url_name in ("main:get_projects_json", "main:get_projects_xml", "main:get_education_json",
                         "main:get_experience_json", "main:show_main", "main:show_experience"):
            self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)
