"""Assignment 5: Education AJAX and the existing owner/editor/member boundaries."""

import uuid

from django.contrib.auth.models import AnonymousUser
from django.test import Client, RequestFactory
from django.urls import reverse

from main.forms import EducationForm
from main.models import Education
from main.tests_assignment3 import education_data
from main.tests_assignment4 import EducationAccounts
from main.views import get_education_json


class EducationAjaxTests(EducationAccounts):
    def test_list_shell_config_and_modal_match_every_role(self):
        for user in (None, self.member, self.staff, self.editor, self.owner):
            self.account(user)
            response = self.client.get(reverse("main:show_education"))
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, self.entry.institution)
            self.assertContains(response, 'id="education-grid"')
            self.assertContains(response, "Loading education")
            self.assertNotIn("education_list", response.context)
            config = response.context["education_config"]
            self.assertEqual(config["isAuthenticated"], user is not None)
            self.assertEqual(config["canManage"], user == self.owner)
            self.assertEqual(config["canEdit"], user in (self.owner, self.editor))
            self.assertTrue(config["csrfToken"])
            assertion = self.assertContains if user == self.owner else self.assertNotContains
            assertion(response, 'id="education-form"')
            if user == self.owner:
                self.assertTemplateUsed(response, "components/education_form_modal.html")
                for field in EducationForm.Meta.fields:
                    self.assertContains(response, f'name="{field}"')

    def test_combined_filters_keep_total_stars_and_only_current_users_membership(self):
        self.entry.starred_by.add(self.member, self.other, self.owner)
        self.completed.starred_by.add(self.other)
        for user, expected in ((self.member, [self.entry]), (self.other, [self.entry]), (self.editor, []), (None, [])):
            self.account(user)
            response = self.client.get(reverse("main:get_education_json"), {
                "q": "  DATA  ", "status": "current", "starred": "1", "user_id": self.other.pk,
            })
            self.assertEqual([item["pk"] for item in response.json()], [str(entry.pk) for entry in expected])
            for item in response.json():
                self.assertEqual(item["fields"]["star_count"], 3)
                self.assertTrue(item["fields"]["is_starred"])
            self.assertIn("Cookie", response["Vary"])

    def test_data_query_cost_is_constant_for_visitors_and_authenticated_users(self):
        for index in range(8):
            entry = Education.objects.create(institution=f"University {index}", degree="Course", start_year=2025, end_year=2025)
            entry.starred_by.add(self.member, self.other)
        for user in (AnonymousUser(), self.member, self.owner):
            request = RequestFactory().get(reverse("main:get_education_json"))
            request.user = user
            with self.assertNumQueries(1):
                response = get_education_json(request)
            self.assertEqual(response.status_code, 200)

    def test_search_configuration_cannot_break_out_of_json_or_input(self):
        payload = '</script><img src=x onerror="alert(1)">'
        response = self.client.get(reverse("main:show_education"), {"q": payload})
        self.assertNotContains(response, payload)
        self.assertContains(response, "\\u003C/script\\u003E")
        self.assertEqual(response.context["education_config"]["initialFilters"]["q"], payload)

    def test_create_owner_returns_201_and_preserves_identity_stars_and_other_records(self):
        self.account(self.owner)
        self.entry.starred_by.add(self.member)
        before = list(Education.objects.values())
        response = self.client.post(reverse("main:create_education_ajax"), education_data(
            id=str(self.entry.pk), starred_by=[self.other.pk], is_superuser="on", groups=[self.editor_group.pk],
        ))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Content-Type"], "application/json")
        created = Education.objects.get(pk=response.json()["pk"])
        self.assertEqual(created.institution, "Example University")
        self.assertNotEqual(created.pk, self.entry.pk)
        self.assertEqual(created.starred_by.count(), 0)
        self.assertEqual(Education.objects.count(), 3)
        self.assertEqual(list(Education.objects.exclude(pk=created.pk).values()), before)
        self.assertEqual(list(self.entry.starred_by.all()), [self.member])
        home = self.client.get(reverse("main:show_main"))
        self.assertContains(home, created.institution)
        records = self.client.get(reverse("main:get_education_json"), {"q": " example ", "status": "completed"}).json()
        self.assertEqual([item["pk"] for item in records], [str(created.pk)])

    def test_create_permission_is_checked_on_server_for_all_nonowners(self):
        for user in (None, self.member, self.editor, self.staff):
            self.account(user)
            self.client.cookies["role"] = "Owner"
            response = self.client.post(reverse("main:create_education_ajax"), education_data(is_superuser="on"))
            self.assertEqual(response.status_code, 403)
            self.assertIn("message", response.json())
            self.assertNotIn("Location", response)
        self.assertEqual(Education.objects.count(), 2)

    def test_revoked_owner_cannot_create_using_an_already_rendered_modal(self):
        self.account(self.owner)
        self.assertContains(self.client.get(reverse("main:show_education")), 'id="education-form"')
        self.owner.is_superuser = False
        self.owner.save()
        response = self.client.post(reverse("main:create_education_ajax"), education_data())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Education.objects.count(), 2)

    def test_ajax_model_form_reports_required_period_numeric_and_url_errors(self):
        self.account(self.owner)
        cases = [({}, "institution"), (education_data(institution="x" * 256), "institution"),
                 (education_data(start_year="1899"), "start_year"), (education_data(start_year="no"), "start_year"),
                 (education_data(end_year="2019"), "end_year"), (education_data(is_current="on"), "end_year"),
                 (education_data(end_year=""), "end_year"), (education_data(display_order="-1"), "display_order"),
                 (education_data(website="javascript:alert(1)"), "website")]
        for data, field in cases:
            with self.subTest(field=field):
                response = self.client.post(reverse("main:create_education_ajax"), data)
                self.assertEqual(response.status_code, 400)
                self.assertIn("message", response.json()["errors"][field][0])
                self.assertIn("code", response.json()["errors"][field][0])
        self.assertEqual(Education.objects.count(), 2)

    def test_ajax_and_regular_create_and_editor_update_share_text_cleaning(self):
        data = education_data(institution=" <b>Clean University</b> ", degree="<i>Course</i>",
                              description='<img src=x onerror="alert(1)">Safe <em>text</em>')
        self.account(self.owner)
        for route, status in (("main:create_education_ajax", 201), ("main:create_education", 302)):
            response = self.client.post(reverse(route), data)
            self.assertEqual(response.status_code, status)
        for entry in Education.objects.filter(institution="Clean University"):
            self.assertEqual(entry.degree, "Course")
            self.assertEqual(entry.description, "Safe text")
        self.assertEqual(Education.objects.filter(institution="Clean University").count(), 2)
        self.account(self.editor)
        response = self.client.post(reverse("main:update_education", args=[self.entry.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.institution, "Clean University")
        self.assertEqual(self.entry.description, "Safe text")

    def test_tag_only_required_fields_are_rejected_and_optional_description_can_be_empty(self):
        self.account(self.owner)
        payload = '<img src="x" onerror="alert(1)">'
        for field in ("institution", "degree"):
            response = self.client.post(reverse("main:create_education_ajax"), education_data(**{field: payload}))
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.json()["errors"])
        self.assertEqual(Education.objects.count(), 2)
        response = self.client.post(reverse("main:create_education_ajax"), education_data(description=payload))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Education.objects.get(pk=response.json()["pk"]).description, "")

    def test_ajax_creation_checks_csrf_before_saving(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        page = client.get(reverse("main:show_education"))
        url = reverse("main:create_education_ajax")
        self.assertEqual(client.post(url, education_data()).status_code, 403)
        self.assertEqual(client.post(url, education_data(), HTTP_X_CSRFTOKEN="invalid").status_code, 403)
        self.assertEqual(Education.objects.count(), 2)
        response = client.post(url, education_data(), HTTP_X_CSRFTOKEN=page.context["education_config"]["csrfToken"])
        self.assertEqual(response.status_code, 201)

    def test_ajax_routes_reject_unsupported_methods(self):
        self.account(self.owner)
        for url in (reverse("main:create_education_ajax"), reverse("main:toggle_education_star_ajax", args=[self.entry.pk])):
            for method in (self.client.get, self.client.head, self.client.put, self.client.delete):
                self.assertEqual(method(url).status_code, 405)
        self.assertEqual(Education.objects.count(), 2)
        self.assertEqual(self.entry.starred_by.count(), 0)

    def test_ajax_star_requires_login_and_changes_only_the_session_account(self):
        url = reverse("main:toggle_education_star_ajax", args=[self.entry.pk])
        self.assertEqual(self.client.post(url).status_code, 403)
        self.entry.starred_by.add(self.other)
        for user in (self.member, self.editor, self.staff, self.owner):
            self.account(user)
            response = self.client.post(url, {"user_id": self.other.pk})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["is_starred"])
            self.assertEqual(response.json()["star_count"], 2)
            self.assertEqual(self.client.get(reverse("main:get_education_json"), {"starred": "1"}).json()[0]["pk"], str(self.entry.pk))
            response = self.client.post(url)
            self.assertFalse(response.json()["is_starred"])
            self.assertEqual(response.json()["star_count"], 1)
            self.assertEqual(self.client.get(reverse("main:get_education_json"), {"starred": "1"}).json(), [])
            self.assertEqual(list(self.entry.starred_by.all()), [self.other])

    def test_ajax_star_csrf_and_missing_entry_have_no_side_effects(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.member)
        page = client.get(reverse("main:show_education"))
        url = reverse("main:toggle_education_star_ajax", args=[self.entry.pk])
        self.assertEqual(client.post(url).status_code, 403)
        token = page.context["education_config"]["csrfToken"]
        missing = client.post(reverse("main:toggle_education_star_ajax", args=[uuid.uuid4()]), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(missing.status_code, 404)
        self.assertIn("message", missing.json())
        self.assertEqual(self.entry.starred_by.count(), 0)
        self.assertEqual(client.post(url, HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(self.entry.starred_by.count(), 1)
