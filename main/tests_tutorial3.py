import uuid
from xml.etree import ElementTree

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from main.forms import ProjectForm
from main.models import Project


def project_data():
    """A new test record, separate from the portfolio fixtures."""
    return {
        "title": "Test Analytics Project",
        "organization": "Example University",
        "context_label": "Practice project",
        "summary": "Analysis of example data.",
        "contribution": "Prepared data and evaluated results.",
        "technologies": "Python\nSQL",
        "award": "",
        "display_order": "2",
    }


class ProjectWriteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(
            username="project-test-owner", is_superuser=True, is_staff=True,
        )
        cls.existing = Project.objects.create(
            title="Existing Portfolio Project",
            organization="Existing Organization",
            summary="Keep this existing summary.",
            contribution="Keep this contribution.",
        )
        cls.other = Project.objects.create(
            title="Another Portfolio Project",
            organization="Another Organization",
            summary="Another summary.",
            contribution="Another contribution.",
        )

    def setUp(self):
        # Tutorial 4: the same write behaviour now requires the owner account.
        self.client.force_login(self.owner)

    def test_create_form_uses_current_fields_and_shared_layout(self):
        response = self.client.get(reverse("main:create_project"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects_form.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertIsInstance(response.context["form"], ProjectForm)
        self.assertContains(response, "Marcel Mikula")
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        for field in ("organization", "summary", "contribution", "technologies"):
            self.assertContains(response, f'name="{field}"')
        self.assertContains(response, '<main id="main-content"', count=1)

    def test_valid_post_saves_once_and_preserves_existing_projects(self):
        data = project_data()
        data["is_featured"] = "on"
        response = self.client.post(reverse("main:create_project"), data, follow=True)

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertEqual(Project.objects.count(), 3)
        created = Project.objects.get(title=data["title"])
        self.assertEqual(created.organization, data["organization"])
        self.assertEqual(created.technology_list, ["Python", "SQL"])
        self.assertEqual(created.display_order, 2)
        self.assertTrue(created.is_featured)
        self.assertContains(response, "Project added successfully.")
        self.assertContains(response, created.title)
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.summary, "Keep this existing summary.")

        # Refreshing the redirected GET does not submit the form again.
        self.client.get(reverse("main:show_projects"))
        self.assertEqual(Project.objects.count(), 3)

    def test_invalid_posts_show_errors_without_saving(self):
        cases = [
            ({}, "title"),
            ({**project_data(), "title": ""}, "title"),
            ({**project_data(), "display_order": "-1"}, "display_order"),
            ({**project_data(), "title": "x" * 256}, "title"),
        ]
        for data, error_field in cases:
            with self.subTest(field=error_field, data=data):
                response = self.client.post(reverse("main:create_project"), data)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].is_bound)
                self.assertIn(error_field, response.context["form"].errors)
                self.assertContains(response, "Please correct the highlighted fields")
                self.assertEqual(Project.objects.count(), 2)
                if data:
                    self.assertContains(response, data["organization"])

    def test_create_requires_a_valid_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        url = reverse("main:create_project")
        self.assertEqual(client.post(url, project_data()).status_code, 403)
        self.assertEqual(Project.objects.count(), 2)

        client.get(url)
        data = {**project_data(), "csrfmiddlewaretoken": client.cookies["csrftoken"].value}
        self.assertEqual(client.post(url, data).status_code, 302)
        self.assertEqual(Project.objects.count(), 3)

    def test_get_cannot_delete_a_project(self):
        url = reverse("main:delete_project", args=[self.existing.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(Project.objects.count(), 2)

    def test_delete_post_removes_only_the_selected_project(self):
        url = reverse("main:delete_project", args=[self.existing.pk])
        response = self.client.post(url, follow=True)

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertFalse(Project.objects.filter(pk=self.existing.pk).exists())
        self.assertTrue(Project.objects.filter(pk=self.other.pk).exists())
        self.assertContains(response, "Project deleted successfully.")

    def test_deleting_a_missing_project_returns_404(self):
        url = reverse("main:delete_project", args=[uuid.uuid4()])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertEqual(Project.objects.count(), 2)

    def test_delete_requires_a_valid_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        url = reverse("main:delete_project", args=[self.existing.pk])
        self.assertEqual(client.post(url).status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.existing.pk).exists())

        client.get(reverse("main:show_projects"))
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post(url, {"csrfmiddlewaretoken": token}).status_code, 302)
        self.assertFalse(Project.objects.filter(pk=self.existing.pk).exists())

    def test_unsupported_write_methods_do_not_change_data(self):
        for url in (
            reverse("main:create_project"),
            reverse("main:delete_project", args=[self.existing.pk]),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.put(url).status_code, 405)
        self.assertEqual(Project.objects.count(), 2)


class ProjectDataDeliveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.featured = Project.objects.create(
            title="Macan Analytics",
            organization="Example Organization",
            summary="Data & quality <review>",
            contribution="Analysed patterns.",
            technologies="Python\nSQL",
            is_featured=True,
            display_order=10,
        )
        cls.other = Project.objects.create(
            title="Explaining AI",
            organization="Another Organization",
            summary="Explanation methods.",
            contribution="Designed examples.",
            display_order=0,
        )

    def test_json_returns_serialized_records_in_model_order(self):
        response = self.client.get(reverse("main:get_projects_json"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        records = response.json()
        self.assertEqual([record["pk"] for record in records], [str(self.featured.pk), str(self.other.pk)])
        self.assertEqual(records[0]["model"], "main.project")
        self.assertEqual(records[0]["fields"]["summary"], self.featured.summary)
        self.assertTrue(records[0]["fields"]["is_featured"])

    def test_title_filter_matches_on_html_json_and_xml(self):
        query = {"title": "  mAcAn  "}
        html = self.client.get(reverse("main:show_projects"), query)
        self.assertEqual(html.context["title_query"], "mAcAn")
        self.assertContains(html, self.featured.title)
        self.assertNotContains(html, self.other.title)
        self.assertContains(html, "Python")
        self.assertContains(html, "SQL")
        self.assertContains(html, 'project-card-featured')

        records = self.client.get(reverse("main:get_projects_json"), query).json()
        self.assertEqual([item["pk"] for item in records], [str(self.featured.pk)])
        xml = self.client.get(reverse("main:get_projects_xml"), query)
        root = ElementTree.fromstring(xml.content)
        self.assertEqual([item.attrib["pk"] for item in root.findall("object")], [str(self.featured.pk)])

        blank = self.client.get(reverse("main:get_projects_json"), {"title": "   "})
        self.assertEqual(len(blank.json()), 2)

    def test_empty_database_and_no_search_results_have_distinct_messages(self):
        query = {"title": "NoSuchTitle"}
        response = self.client.get(reverse("main:show_projects"), query)
        self.assertContains(response, "No projects match your search.")
        self.assertNotContains(response, "No projects have been added yet.")
        self.assertEqual(self.client.get(reverse("main:get_projects_json"), query).json(), [])
        self.assertEqual(Project.objects.count(), 2)

        Project.objects.all().delete()
        response = self.client.get(reverse("main:show_projects"))
        self.assertContains(response, "No projects have been added yet.")
        self.assertEqual(self.client.get(reverse("main:get_projects_json")).json(), [])
        xml = self.client.get(reverse("main:get_projects_xml"))
        self.assertEqual(ElementTree.fromstring(xml.content).findall("object"), [])

    def test_xml_returns_parseable_data_with_special_characters(self):
        response = self.client.get(reverse("main:get_projects_xml"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml")
        root = ElementTree.fromstring(response.content)
        self.assertEqual(root.tag, "django-objects")
        records = root.findall("object")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].attrib["pk"], str(self.featured.pk))
        fields = {field.attrib["name"]: field.text for field in records[0].findall("field")}
        self.assertEqual(fields["summary"], self.featured.summary)

    def test_data_endpoints_reject_post_without_changing_data(self):
        for name in ("main:get_projects_json", "main:get_projects_xml"):
            with self.subTest(name=name):
                self.assertEqual(self.client.post(reverse(name)).status_code, 405)
        self.assertEqual(Project.objects.count(), 2)
