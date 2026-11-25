from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from main.models import Project


class MobileProjectApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_superuser("mobile-owner", password="local-test-only")
        cls.member = get_user_model().objects.create_user("mobile-member", password="local-test-only")
        cls.old = Project.objects.create(title="Existing project", organization="UI", summary="Original",
                                         contribution="Analysis", technologies="Django\nFlutter")

    def login(self, username):
        response = self.client.post(reverse("api:api_token_auth"), {
            "username": username, "password": "local-test-only",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        return response.data["token"]

    def test_owner_round_trip_and_revocation_without_affecting_other_tokens(self):
        url = reverse("api:project_list")
        public = self.client.get(url).data[0]
        self.assertEqual((public["description"], public["tech_stack"], public["project_url"]),
                         ("Original", "Django\nFlutter", ""))
        payload = {"title": "New", "description": "A <b>mobile</b> entry", "tech_stack": "Dart",
                   "project_url": "https://example.org/new", "project_image_url": "https://example.org/photo.png"}
        member = self.login("mobile-member")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {member}")
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 403)
        owner = self.login("mobile-owner")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {owner}")
        created = self.client.post(url, payload, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        row = Project.objects.get(pk=created.data["id"])
        self.assertEqual((row.summary, row.technologies, row.project_url, row.project_image_url),
                         ("A mobile entry", "Dart", payload["project_url"], payload["project_image_url"]))
        row.full_clean()
        self.assertEqual(created.data["description"], row.summary)
        self.assertEqual(self.client.post(reverse("api:api_logout")).status_code, 204)
        self.assertEqual(self.client.post(url, payload, format="json").status_code, 401)
        self.assertTrue(Token.objects.filter(key=member).exists())
        self.client.credentials()
        self.assertEqual(len(self.client.get(url).data), 2)

    def test_form_validation_optional_image_and_invalid_login(self):
        auth = reverse("api:api_token_auth")
        self.assertEqual(self.client.post(auth, {"username": "mobile-owner", "password": "wrong"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(reverse("api:api_logout")).status_code, 401)
        token = self.login("mobile-owner")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        payload = {"title": "Field test", "description": "Description", "tech_stack": "Dart",
                   "project_url": "https://example.org/project"}
        url = reverse("api:project_list")
        for key, bad in (("project_url", "invalid"), ("project_image_url", "image"),
                         ("description", "<br>"), ("tech_stack", "")):
            response = self.client.post(url, {**payload, key: bad}, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn(key, response.data)
        created = self.client.post(url, payload, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["project_image_url"], "")

    def test_chrome_preflight_and_unchanged_browser_session(self):
        url = reverse("api:project_list")
        kwargs = {"HTTP_ACCESS_CONTROL_REQUEST_METHOD": "POST",
                  "HTTP_ACCESS_CONTROL_REQUEST_HEADERS": "authorization,content-type"}
        with self.settings(CORS_ALLOWED_ORIGIN_REGEXES=[r"^http://localhost:\d+$"]):
            response = self.client.options(url, HTTP_ORIGIN="http://localhost:52345", **kwargs)
            self.assertEqual(response["Access-Control-Allow-Origin"], "http://localhost:52345")
            self.assertIn("authorization", response["Access-Control-Allow-Headers"])
            self.assertNotIn("Access-Control-Allow-Origin", self.client.options(url, HTTP_ORIGIN="https://unknown.example", **kwargs))
        token = self.login("mobile-member")
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(reverse("api:api_logout")).status_code, 204)
        self.assertTrue(Token.objects.filter(key=token).exists())
        self.assertIn("_auth_user_id", self.client.session)
