from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.management import call_command
from datetime import datetime

from main.models import Experience, Project


class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="PBP Teaching Assistant",
            description="Help students understand web development.",
            category="part-time",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/a-page-that-does-not-exist/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "PBP Teaching Assistant")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Ongoing")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "No experience has been added yet.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Completed")
        self.assertNotContains(response, "Ongoing")

class ProjectPageTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="Example Analytics Project",
            organization="Example University",
            context_label="University project",
            summary="An analysis of example business data.",
            contribution="I prepared and evaluated the data.",
            technologies="Python\nSQL",
        )

    def test_projects_page_loads_model_data_from_json(self):
        response = self.client.get(reverse("main:show_projects"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects.html")
        self.assertContains(response, 'id="project-grid"')
        self.assertNotContains(response, self.project.title)
        data = self.client.get(reverse("main:get_projects_json")).json()[0]["fields"]
        for name in ("title", "organization", "summary", "contribution"):
            self.assertEqual(data[name], getattr(self.project, name))
        self.assertEqual(data["technology_list"], ["Python", "SQL"])

    def test_empty_projects_page(self):
        Project.objects.all().delete()

        response = self.client.get(reverse("main:show_projects"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No projects have been added yet.")

    def test_existing_pages_link_to_projects(self):
        for route in ("main:show_main", "main:show_experience"):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))

                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    f'href="{reverse("main:show_projects")}"',
                )

class ProjectDetailTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="Selected Analytics Project",
            organization="Example University",
            summary="An analysis of example business data.",
            contribution="I prepared and evaluated the data.",
            technologies="Python\nSQL",
        )
        self.other_project = Project.objects.create(
            title="Another Independent Project",
            organization="Another Organization",
            summary="A different project summary.",
            contribution="A different contribution.",
        )

    def test_detail_page_displays_only_the_selected_project(self):
        url = reverse(
            "main:show_project_detail",
            kwargs={"project_id": self.project.pk},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "project_detail.html")
        self.assertContains(response, self.project.title)
        self.assertContains(response, self.project.organization)
        self.assertContains(response, self.project.summary)
        self.assertContains(response, self.project.contribution)
        self.assertContains(response, "Python")
        self.assertContains(response, "SQL")
        self.assertNotContains(response, self.other_project.title)
        self.assertContains(
            response,
            f'href="{reverse("main:show_projects")}"',
        )

    def test_missing_project_returns_404(self):
        project_id = self.project.pk
        self.project.delete()

        url = reverse(
            "main:show_project_detail",
            kwargs={"project_id": project_id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_project_list_links_to_each_detail_page(self):
        records = self.client.get(reverse("main:get_projects_json")).json()
        links = {item["pk"]: item["urls"]["detail"] for item in records}

        for project in (self.project, self.other_project):
            with self.subTest(project=project.title):
                url = reverse(
                    "main:show_project_detail",
                    kwargs={"project_id": project.pk},
                )
                self.assertEqual(links[str(project.pk)], url)
                self.assertEqual(self.client.get(url).status_code, 200)


class ProjectFixtureTests(TestCase):
    def test_reloading_projects_preserves_other_data_without_duplicates(self):
        custom_project = Project.objects.create(
            title="My Additional Project",
            organization="Independent",
            summary="An independently added project.",
            contribution="My own contribution.",
        )

        for _ in range(2):
            call_command("loaddata", "main/projects.json", verbosity=0)

        self.assertEqual(Project.objects.count(), 4)
        custom_project.refresh_from_db()
        self.assertEqual(custom_project.summary, "An independently added project.")

class ExperienceHistoryTests(TestCase):
    def test_historical_experience_is_saved_and_displayed(self):
        started_at = timezone.make_aware(datetime(2022, 9, 1))
        ended_at = timezone.make_aware(datetime(2023, 8, 1))

        experience = Experience.objects.create(
            title="Example IT Role",
            organization="Example Company",
            description="Prepared reports.\nBuilt dashboards.",
            role_timeline="Internship followed by a working student role.",
            category="intern-working",
            started_at=started_at,
            ended_at=ended_at,
        )
        experience.refresh_from_db()

        self.assertEqual(experience.started_at, started_at)
        self.assertEqual(experience.ended_at, ended_at)

        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, experience.organization)
        self.assertContains(response, experience.role_timeline)
        self.assertContains(response, "September 2022")
        self.assertContains(response, "August 2023")
        self.assertContains(response, "Prepared reports.")
        self.assertContains(response, "Built dashboards.")
        self.assertContains(response, "Completed")
