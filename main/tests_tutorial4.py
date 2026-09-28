"""Authentication, permission boundaries, sessions, cookies and project stars."""

import uuid
from xml.etree import ElementTree

from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from main.models import Education, Project
from main.tests_tutorial3 import project_data


# These credentials exist only in Django's temporary test database.
TEST_PASSWORD = "Practice-only-8hX!4mQz"


class AuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.visitor = get_user_model().objects.create_user(
            username="test-visitor", password=TEST_PASSWORD,
        )

    def login_data(self):
        return {"username": self.visitor.username, "password": TEST_PASSWORD}

    def test_public_pages_and_registration_login_navigation(self):
        for name in ("show_main", "show_projects", "show_experience", "show_education"):
            with self.subTest(page=name):
                response = self.client.get(reverse(f"main:{name}"))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f'href="{reverse("main:login")}"')
                self.assertContains(response, f'href="{reverse("main:register")}"')
                self.assertNotContains(response, 'class="nav-user"')

    def test_auth_forms_extend_the_existing_layout_once(self):
        for name in ("register", "login"):
            response = self.client.get(reverse(f"main:{name}"))
            self.assertTemplateUsed(response, "base.html")
            self.assertTemplateUsed(response, "components/form_fields.html")
            self.assertContains(response, '<main id="main-content"', count=1)
            self.assertContains(response, 'name="csrfmiddlewaretoken"')
            self.assertFalse(response.context["form"].is_bound)

    def test_registration_hashes_password_and_never_grants_owner_rights(self):
        response = self.client.post(reverse("main:register"), {
            "username": "new-visitor", "password1": TEST_PASSWORD,
            "password2": TEST_PASSWORD, "is_superuser": "on", "is_staff": "on",
        }, follow=True)
        self.assertRedirects(response, reverse("main:login"))
        account = get_user_model().objects.get(username="new-visitor")
        self.assertTrue(account.check_password(TEST_PASSWORD))
        self.assertNotEqual(account.password, TEST_PASSWORD)
        self.assertFalse(account.is_superuser)
        self.assertFalse(account.is_staff)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertContains(response, "Account created successfully. Please log in.")

    def test_invalid_registration_and_empty_post_show_errors_without_creating_accounts(self):
        cases = [
            {},
            {"username": "test-visitor", "password1": TEST_PASSWORD, "password2": TEST_PASSWORD},
            {"username": "new", "password1": TEST_PASSWORD, "password2": "Different-password-7!"},
            {"username": "new", "password1": "123", "password2": "123"},
        ]
        for data in cases:
            with self.subTest(data=data):
                response = self.client.post(reverse("main:register"), data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].is_bound)
                self.assertTrue(response.context["form"].errors)
                self.assertContains(response, "Please correct the highlighted fields")
                self.assertEqual(get_user_model().objects.count(), 1)

    def test_invalid_login_and_empty_post_do_not_create_a_session(self):
        for data in ({}, {**self.login_data(), "password": "wrong"}):
            response = self.client.post(reverse("main:login"), data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].is_bound)
            self.assertTrue(response.context["form"].errors)
            self.assertNotIn(SESSION_KEY, self.client.session)
            self.assertNotIn("last_login", response.cookies)

    def test_login_sets_session_cookie_timestamp_and_keeps_owner_profile(self):
        response = self.client.post(reverse("main:login"), self.login_data())
        self.assertRedirects(response, reverse("main:show_main"))
        self.assertEqual(self.client.session[SESSION_KEY], str(self.visitor.pk))
        self.assertIn("sessionid", response.cookies)
        cookie = response.cookies["last_login"]
        self.assertRegex(cookie.value, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC$")
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        for name in ("show_main", "show_projects", "show_experience", "show_education"):
            page = self.client.get(reverse(f"main:{name}"))
            self.assertContains(page, 'class="nav-user">test-visitor</span>')
            self.assertContains(page, "Marcel Mikula")
        home = self.client.get(reverse("main:show_main"))
        self.assertEqual(home.context["last_login"], cookie.value)
        self.assertContains(home, cookie.value)

    @override_settings(DEBUG=False)
    def test_production_login_cookie_is_secure(self):
        response = self.client.post(reverse("main:login"), self.login_data())
        self.assertTrue(response.cookies["last_login"]["secure"])

    def test_inactive_account_cannot_log_in(self):
        self.visitor.is_active = False
        self.visitor.save()
        response = self.client.post(reverse("main:login"), self.login_data())
        self.assertTrue(response.context["form"].errors)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_logout_clears_session_and_timestamp_but_preserves_account_and_stars(self):
        project = Project.objects.create(
            title="Persistent project", organization="Example",
            summary="Summary", contribution="Contribution",
        )
        project.starred_by.add(self.visitor)
        self.client.post(reverse("main:login"), self.login_data())
        response = self.client.post(reverse("main:logout"))
        self.assertRedirects(response, reverse("main:show_main"))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(response.cookies["last_login"]["max-age"], 0)
        self.assertEqual(response.cookies["sessionid"]["max-age"], 0)
        self.assertTrue(get_user_model().objects.filter(pk=self.visitor.pk).exists())
        self.assertTrue(project.starred_by.filter(pk=self.visitor.pk).exists())
        self.assertContains(self.client.get(reverse("main:show_main")), "No active login session / Cookie not found")
        self.assertRedirects(self.client.post(reverse("main:login"), self.login_data()), reverse("main:show_main"))

    def test_logout_get_does_not_end_the_session(self):
        self.client.force_login(self.visitor)
        self.assertEqual(self.client.get(reverse("main:logout")).status_code, 405)
        self.assertIn(SESSION_KEY, self.client.session)

    def test_authentication_posts_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        for name in ("register", "login", "logout"):
            self.assertEqual(client.post(reverse(f"main:{name}"), {}).status_code, 403)
        client.get(reverse("main:login"))
        response = client.post(reverse("main:login"), {
            **self.login_data(), "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        })
        self.assertEqual(response.status_code, 302)
        # Login rotates the CSRF token; use the newly issued cookie.
        response = client.post(reverse("main:logout"), {
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
        })
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(SESSION_KEY, client.session)

    def test_cookie_text_is_escaped_and_does_not_grant_access(self):
        self.client.cookies["last_login"] = "<script>alert(1)</script>"
        home = self.client.get(reverse("main:show_main"))
        self.assertNotContains(home, "<script>")
        self.assertContains(home, "&lt;script&gt;")
        self.assertNotIn(SESSION_KEY, self.client.session)
        response = self.client.get(reverse("main:create_project"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("main:login")))


class AuthorizationAndStarTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        accounts = get_user_model().objects
        cls.visitor = accounts.create_user(username="star-user")
        cls.other = accounts.create_user(username="other-user")
        cls.staff = accounts.create_user(username="staff-without-owner-role", is_staff=True)
        cls.owner = accounts.create_user(username="owner", is_superuser=True, is_staff=True)
        cls.project = Project.objects.create(
            title="Star Test Project", organization="Example",
            summary="Summary", contribution="Contribution",
        )
        cls.education = Education.objects.create(
            institution="Existing University", degree="M.Sc.", start_year=2024,
            is_current=True,
        )

    def write_urls(self):
        return [
            reverse("main:create_project"),
            reverse("main:delete_project", args=[self.project.pk]),
            reverse("main:create_education"),
            reverse("main:update_education", args=[self.education.pk]),
            reverse("main:delete_education", args=[self.education.pk]),
        ]

    def test_anonymous_writes_redirect_to_login_and_preserve_data(self):
        for url in self.write_urls():
            with self.subTest(url=url):
                response = self.client.post(url, project_data())
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("main:login") + "?next="))
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Education.objects.count(), 1)

    def test_regular_and_staff_accounts_cannot_write_even_using_direct_urls(self):
        for account in (self.visitor, self.staff):
            self.client.force_login(account)
            for url in self.write_urls():
                with self.subTest(account=account.username, url=url):
                    self.assertEqual(self.client.post(url, project_data()).status_code, 403)
            for name in ("main:create_project", "main:create_education"):
                self.assertEqual(self.client.get(reverse(name)).status_code, 403)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Education.objects.count(), 1)

    def test_management_controls_match_permissions(self):
        for account in (None, self.visitor, self.owner):
            self.client.logout()
            if account:
                self.client.force_login(account)
            projects = self.client.get(reverse("main:show_projects"))
            education = self.client.get(reverse("main:show_education"))
            project_add = f'href="{reverse("main:create_project")}"'
            education_add = f'href="{reverse("main:create_education")}"'
            if account == self.owner:
                self.assertContains(projects, project_add)
                self.assertContains(projects, f'popovertarget="delete-project-{self.project.pk}"')
                self.assertContains(education, education_add)
                self.assertContains(education, f'href="{reverse("main:update_education", args=[self.education.pk])}"')
            else:
                self.assertNotContains(projects, project_add)
                self.assertNotContains(projects, f'popovertarget="delete-project-{self.project.pk}"')
                self.assertNotContains(education, education_add)
                self.assertNotContains(education, f'href="{reverse("main:update_education", args=[self.education.pk])}"')
            self.assertContains(projects, f'action="{reverse("main:toggle_star", args=[self.project.pk])}"')

    def test_guest_star_redirects_without_changing_membership(self):
        response = self.client.post(reverse("main:toggle_star", args=[self.project.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("main:login")))
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_star_and_unstar_affect_only_the_current_account(self):
        self.project.starred_by.add(self.other)
        self.client.force_login(self.visitor)
        url = reverse("main:toggle_star", args=[self.project.pk])
        response = self.client.post(url, {"user_id": self.other.pk}, follow=True)
        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertEqual(self.project.starred_by.count(), 2)
        self.assertContains(response, 'aria-pressed="true"')
        self.assertContains(response, "Unstar")
        self.assertContains(response, 'class="star-count">2</span>')
        self.assertContains(response, "star-user")
        self.assertContains(response, "other-user")
        self.client.get(reverse("main:show_projects"))
        self.assertEqual(self.project.starred_by.count(), 2)
        response = self.client.post(url, follow=True)
        self.assertContains(response, 'aria-pressed="false"')
        self.assertEqual(list(self.project.starred_by.values_list("pk", flat=True)), [self.other.pk])

    def test_owner_can_star_too(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("main:toggle_star", args=[self.project.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.owner.starred_projects.filter(pk=self.project.pk).exists())

    def test_star_endpoint_is_post_only_and_missing_project_returns_404(self):
        self.client.force_login(self.visitor)
        url = reverse("main:toggle_star", args=[self.project.pk])
        for method in (self.client.get, self.client.head, self.client.put, self.client.delete):
            self.assertEqual(method(url).status_code, 405)
        self.assertEqual(self.project.starred_by.count(), 0)
        missing_url = reverse("main:toggle_star", args=[uuid.uuid4()])
        self.assertEqual(self.client.post(missing_url).status_code, 404)

    def test_star_requires_csrf_even_with_an_authenticated_session(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.visitor)
        url = reverse("main:toggle_star", args=[self.project.pk])
        self.assertEqual(client.post(url).status_code, 403)
        self.assertEqual(self.project.starred_by.count(), 0)
        client.get(reverse("main:show_projects"))
        response = client.post(url, {"csrfmiddlewaretoken": client.cookies["csrftoken"].value})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.starred_by.count(), 1)

    def test_repeated_add_has_no_duplicates_and_new_project_starts_without_stars(self):
        self.project.starred_by.add(self.visitor)
        self.project.starred_by.add(self.visitor)
        self.assertEqual(self.project.starred_by.count(), 1)
        self.client.force_login(self.owner)
        data = {**project_data(), "starred_by": [self.visitor.pk]}
        self.assertEqual(self.client.post(reverse("main:create_project"), data).status_code, 302)
        self.assertEqual(Project.objects.get(title=data["title"]).starred_by.count(), 0)

    def test_public_json_and_xml_use_usernames_without_account_secrets(self):
        self.project.starred_by.add(self.visitor, self.other)
        response = self.client.get(reverse("main:get_projects_json"))
        self.assertEqual(response["Content-Type"], "application/json")
        names = response.json()[0]["fields"]["starred_by"]
        self.assertCountEqual(names, [["star-user"], ["other-user"]])
        self.assertNotContains(response, "password")
        self.assertNotContains(response, "is_superuser")
        xml = self.client.get(reverse("main:get_projects_xml"))
        root = ElementTree.fromstring(xml.content)
        self.assertCountEqual([node.text for node in root.findall(".//natural")], ["star-user", "other-user"])
        html = self.client.get(reverse("main:show_projects"), {"title": " star test "})
        self.assertContains(html, self.project.title)
        self.assertContains(html, 'class="star-count">2</span>')
        self.assertContains(html, "star-user")
        self.assertContains(html, "other-user")
