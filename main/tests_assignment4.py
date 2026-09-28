"""Assignment 4: role boundaries, private stars, public data, and regressions."""

import uuid
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import serializers
from django.test import Client, TestCase
from django.urls import reverse

from main.models import Education, Project
from main.tests_assignment3 import education_data
from main.tests_tutorial4 import TEST_PASSWORD
from main.views import _attach_education_star_state


class EducationAccounts(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(username="education-owner", is_superuser=True, is_staff=True)
        cls.member = users.create_user(username="education-member", email="private@example.test")
        cls.other = users.create_user(username="another-member")
        cls.editor = users.create_user(username="education-editor")
        cls.staff = users.create_user(username="education-staff", is_staff=True)
        cls.editor_group = Group.objects.create(name="Editor")
        cls.editor.groups.add(cls.editor_group)
        cls.entry = Education.objects.create(
            institution="Current University", degree="M.Sc. Data Science",
            start_year=2024, is_current=True,
        )
        cls.completed = Education.objects.create(
            institution="Earlier University", degree="B.Sc. Information Systems",
            start_year=2020, end_year=2023, display_order=1,
        )
        cls.project = Project.objects.create(
            title="Existing project", organization="Example",
            summary="Summary", contribution="Contribution",
        )

    def account(self, user):
        self.client.logout()
        if user:
            self.client.force_login(user)

    def detail_url(self):
        return reverse("main:show_education_detail", args=[self.entry.pk])

    def star_url(self):
        return reverse("main:toggle_education_star", args=[self.entry.pk])


class EducationPermissionTests(EducationAccounts):
    def test_read_pages_and_detail_remain_public_for_every_role(self):
        for user in (None, self.member, self.staff, self.editor, self.owner):
            self.account(user)
            for url in (reverse("main:show_education"), self.detail_url(),
                        reverse("main:get_education_json")):
                with self.subTest(user=user, url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, self.entry.institution)

    def test_direct_write_requests_enforce_the_four_roles(self):
        create = reverse("main:create_education")
        update = reverse("main:update_education", args=[self.entry.pk])
        delete = reverse("main:delete_education", args=[self.entry.pk])
        before = list(Education.objects.values())
        for user in (None, self.member, self.staff, self.editor):
            self.account(user)
            urls = [create, delete] if user == self.editor else [create, update, delete]
            for url in urls:
                with self.subTest(user=user, url=url):
                    response = self.client.post(url, education_data())
                    if user is None:
                        self.assertEqual(response.status_code, 302)
                        self.assertTrue(response.url.startswith(reverse("main:login") + "?next="))
                    else:
                        self.assertEqual(response.status_code, 403)
                    if url != delete:
                        self.assertEqual(self.client.get(url).status_code, 302 if user is None else 403)
        self.assertEqual(list(Education.objects.values()), before)

    def test_owner_and_editor_update_only_the_selected_entry(self):
        self.entry.starred_by.add(self.member)
        original_id = self.entry.pk
        created_at = self.entry.created_at
        for user in (self.editor, self.owner):
            self.account(user)
            url = reverse("main:update_education", args=[original_id])
            self.assertEqual(self.client.get(url).status_code, 200)
            response = self.client.post(url, education_data(
                institution="Updated University", id=str(self.completed.pk),
                starred_by=[self.other.pk], is_superuser="on", groups=[self.editor_group.pk],
            ), follow=True)
            self.assertRedirects(response, reverse("main:show_education"))
            self.entry.refresh_from_db()
            self.completed.refresh_from_db()
            self.assertEqual(self.entry.pk, original_id)
            self.assertEqual(self.entry.created_at, created_at)
            self.assertEqual(self.entry.institution, "Updated University")
            self.assertEqual(self.completed.institution, "Earlier University")
            self.assertEqual(Education.objects.count(), 2)
            self.assertEqual(list(self.entry.starred_by.all()), [self.member])
        self.editor.refresh_from_db()
        self.assertFalse(self.editor.is_superuser)

    def test_editor_invalid_update_preserves_data_and_shows_errors(self):
        self.account(self.editor)
        response = self.client.post(
            reverse("main:update_education", args=[self.entry.pk]),
            education_data(end_year="2010"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("end_year", response.context["form"].errors)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.institution, "Current University")

    def test_controls_match_roles_on_both_list_and_detail(self):
        for user, role in ((None, "Visitor"), (self.member, "Member"),
                           (self.staff, "Member"), (self.editor, "Editor"), (self.owner, "Owner")):
            self.account(user)
            for url in (reverse("main:show_education"), self.detail_url()):
                response = self.client.get(url)
                self.assertContains(response, f'class="education-role">{role}</span>')
                edit = f'href="{reverse("main:update_education", args=[self.entry.pk])}"'
                delete = f'action="{reverse("main:delete_education", args=[self.entry.pk])}"'
                (self.assertContains if user in (self.editor, self.owner) else self.assertNotContains)(response, edit)
                (self.assertContains if user == self.owner else self.assertNotContains)(response, delete)
                self.assertContains(response, f'action="{self.star_url()}"')
            listing = self.client.get(reverse("main:show_education"))
            add = f'href="{reverse("main:create_education")}"'
            (self.assertContains if user == self.owner else self.assertNotContains)(listing, add)

    def test_group_removal_revokes_editor_access_on_the_next_request(self):
        self.account(self.editor)
        url = reverse("main:update_education", args=[self.entry.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.editor.groups.remove(self.editor_group)
        self.assertEqual(self.client.post(url, education_data()).status_code, 403)
        self.assertNotContains(self.client.get(reverse("main:show_education")), f'href="{url}"')

    def test_public_registration_and_forged_cookies_cannot_grant_editor_access(self):
        response = self.client.post(reverse("main:register"), {
            "username": "cannot-pick-a-role", "password1": TEST_PASSWORD,
            "password2": TEST_PASSWORD, "groups": [self.editor_group.pk],
            "role": "Editor", "is_staff": "on", "is_superuser": "on",
        })
        self.assertRedirects(response, reverse("main:login"))
        user = get_user_model().objects.get(username="cannot-pick-a-role")
        self.assertFalse(user.groups.exists())
        self.assertFalse(user.is_staff or user.is_superuser)
        self.account(user)
        self.client.cookies["role"] = "Editor"
        self.client.cookies["is_superuser"] = "True"
        self.assertEqual(self.client.post(
            reverse("main:update_education", args=[self.entry.pk]), education_data(),
        ).status_code, 403)

    def test_owner_assigns_editor_membership_through_django_admin(self):
        self.account(self.owner)
        url = reverse("admin:auth_user_change", args=[self.member.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, {
            "username": self.member.username, "email": self.member.email,
            "first_name": "", "last_name": "", "is_active": "on",
            "groups": [self.editor_group.pk], "user_permissions": [],
            "date_joined_0": self.member.date_joined.strftime("%Y-%m-%d"),
            "date_joined_1": self.member.date_joined.strftime("%H:%M:%S"),
            "_save": "Save",
        })
        self.assertEqual(response.status_code, 302)
        self.member.refresh_from_db()
        self.assertTrue(self.member.groups.filter(name="Editor").exists())
        self.assertFalse(self.member.is_staff or self.member.is_superuser)
        self.account(self.member)
        self.assertEqual(self.client.get(reverse(
            "main:update_education", args=[self.entry.pk],
        )).status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 302)
        self.account(self.staff)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_editor_cannot_create_or_delete_projects(self):
        self.account(self.editor)
        for url in (reverse("main:create_project"),
                    reverse("main:delete_project", args=[self.project.pk])):
            self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.pk).exists())


class EducationStarTests(EducationAccounts):
    def test_guest_redirects_and_each_authenticated_role_can_star(self):
        response = self.client.post(self.star_url())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("main:login")))
        self.assertEqual(self.entry.starred_by.count(), 0)
        for user in (self.member, self.editor, self.staff, self.owner):
            self.account(user)
            response = self.client.post(self.star_url())
            self.assertRedirects(response, reverse("main:show_education"))
            self.assertTrue(user.starred_education.filter(pk=self.entry.pk).exists())
        self.assertEqual(self.entry.starred_by.count(), 4)

    def test_star_unstar_only_changes_the_session_users_membership(self):
        before = list(Education.objects.values())
        self.entry.starred_by.add(self.other, self.other)
        self.account(self.member)
        response = self.client.post(self.star_url(), {"user_id": self.other.pk}, follow=True)
        self.assertContains(response, "Star added: Current University.")
        self.assertEqual(self.entry.starred_by.count(), 2)
        for url in (reverse("main:show_education"), self.detail_url()):
            response = self.client.get(url)
            self.assertContains(response, 'aria-pressed="true"')
            self.assertContains(response, 'class="star-count">2</span>')
        response = self.client.post(self.star_url(), follow=True)
        self.assertContains(response, "Star removed: Current University.")
        self.assertEqual(list(self.entry.starred_by.all()), [self.other])
        self.assertEqual(list(Education.objects.values()), before)
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_star_and_editor_update_require_valid_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.editor)
        update = reverse("main:update_education", args=[self.entry.pk])
        for url in (self.star_url(), update):
            self.assertEqual(client.post(url, education_data()).status_code, 403)
        self.assertEqual(self.entry.starred_by.count(), 0)
        client.get(reverse("main:show_education"))
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post(self.star_url(), {"csrfmiddlewaretoken": token}).status_code, 302)
        self.assertEqual(client.post(update, {
            **education_data(), "csrfmiddlewaretoken": token,
        }).status_code, 302)

    def test_unsupported_methods_and_missing_ids_do_not_change_data(self):
        self.account(self.member)
        for method in (self.client.get, self.client.head, self.client.put, self.client.delete):
            self.assertEqual(method(self.star_url()).status_code, 405)
        self.assertEqual(self.client.post(reverse(
            "main:toggle_education_star", args=[uuid.uuid4()],
        )).status_code, 404)
        self.assertEqual(self.client.post("/education/not-a-uuid/star/").status_code, 404)
        self.assertEqual(self.entry.starred_by.count(), 0)

    def test_star_returns_to_detail_or_preserves_filters_without_open_redirects(self):
        self.account(self.member)
        response = self.client.post(self.star_url(), {"return_to": "detail"})
        self.assertRedirects(response, self.detail_url())
        response = self.client.post(self.star_url(), {
            "q": "  Current & University  ", "status": "current", "starred": "1",
            "next": "https://example.org/", "return_to": "https://example.org/",
        })
        destination = urlsplit(response.url)
        self.assertEqual(destination.netloc, "")
        self.assertEqual(destination.path, reverse("main:show_education"))
        self.assertEqual(parse_qs(destination.query), {
            "q": ["Current & University"], "status": ["current"], "starred": ["1"],
        })
        response = self.client.post(self.star_url(), {"status": "invalid", "starred": "99"})
        self.assertRedirects(response, reverse("main:show_education"))

    def test_unstarring_from_personal_filter_updates_count_and_empty_state(self):
        self.account(self.member)
        self.entry.starred_by.add(self.member)
        response = self.client.post(self.star_url(), {"starred": "1"}, follow=True)
        self.assertRedirects(response, reverse("main:show_education") + "?starred=1")
        self.assertContains(response, "No starred education entries match these filters.")
        self.assertContains(response, "0 entries")
        self.assertContains(response, '<option value="1" selected>My starred entries</option>', html=True)

    def test_account_deletion_removes_stars_without_deleting_portfolio_records(self):
        self.entry.starred_by.add(self.member, self.other)
        self.member.delete()
        self.assertEqual(list(self.entry.starred_by.all()), [self.other])
        self.assertEqual(Education.objects.count(), 2)


class EducationStarDataTests(EducationAccounts):
    def test_api_preserves_public_fields_and_omits_all_star_account_information(self):
        self.entry.starred_by.add(self.member)
        expected_fields = {
            "institution", "degree", "description", "start_year", "end_year",
            "is_current", "website", "display_order", "created_at", "updated_at",
        }
        for user in (None, self.member, self.editor, self.owner):
            self.account(user)
            response = self.client.get(reverse("main:get_education_json"))
            self.assertEqual(response["Content-Type"], "application/json")
            self.assertIn("Cookie", response["Vary"])
            for item in response.json():
                self.assertEqual(set(item), {"model", "pk", "fields"})
                self.assertEqual(set(item["fields"]), expected_fields)
            self.assertNotContains(response, self.member.username)
            self.assertNotContains(response, self.member.email)
            self.assertNotContains(response, "starred_by")
            restored = list(serializers.deserialize("json", response.content))
            self.assertEqual(restored[0].object.period_label, self.entry.period_label)

    def test_personal_star_filter_matches_html_json_and_combines_with_search(self):
        self.entry.starred_by.add(self.member)
        self.completed.starred_by.add(self.other)
        for user, parameters, expected in (
            (None, {"starred": "1"}, []),
            (self.member, {"starred": "1"}, [self.entry.pk]),
            (self.other, {"starred": "1"}, [self.completed.pk]),
            (self.member, {"starred": "1", "q": "  cURrENt  ", "status": "current"}, [self.entry.pk]),
            (self.member, {"starred": "1", "status": "completed"}, []),
            (self.member, {"starred": "1", "user_id": self.other.pk}, [self.entry.pk]),
        ):
            self.account(user)
            html = self.client.get(reverse("main:show_education"), parameters)
            data = self.client.get(reverse("main:get_education_json"), parameters)
            self.assertEqual([entry.pk for entry in html.context["education_list"]], expected)
            self.assertEqual([entry["pk"] for entry in data.json()], [str(pk) for pk in expected])

    def test_detail_uses_shared_layout_escapes_content_and_is_read_only(self):
        self.entry.institution = '<script>alert("x")</script>'
        self.entry.save()
        response = self.client.get(self.detail_url())
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "components/education_card.html")
        self.assertContains(response, "<!DOCTYPE html>", count=1)
        self.assertContains(response, '<main id="main-content"', count=1)
        self.assertNotContains(response, self.entry.institution)
        self.assertContains(response, "&lt;script&gt;")
        self.assertContains(response, 'name="return_to" value="detail"')
        self.assertEqual(self.client.post(self.detail_url()).status_code, 405)
        self.assertEqual(self.client.get(reverse(
            "main:show_education_detail", args=[uuid.uuid4()],
        )).status_code, 404)

    def test_star_state_is_loaded_in_one_query_for_the_whole_page(self):
        self.entry.starred_by.add(self.member, self.other)
        for index in range(8):
            Education.objects.create(
                institution=f"Additional University {index}", degree="Course",
                start_year=2022, end_year=2022,
            )
        entries = list(Education.objects.all())
        with self.assertNumQueries(1):
            _attach_education_star_state(entries, self.member)
            state = {entry.pk: (entry.star_count, entry.is_starred) for entry in entries}
        self.assertEqual(state[self.entry.pk], (2, True))
        self.assertEqual(state[self.completed.pk], (0, False))
