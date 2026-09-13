from django.shortcuts import get_object_or_404, render

from main.models import Experience, Project


PROFILE = {
    "name": "Marcel Mikula",
    "npm": "2606816592",
    "study_program": "Business Information Systems",
    "bio": (
        "A Business Information Systems student from Germany, "
        "currently completing an exchange semester at Universitas Indonesia."
    ),
}


def show_main(request):
    return render(request, "index.html", PROFILE)


def show_experience(request):
    context = {
        "name": PROFILE["name"],
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)


def show_projects(request):
    context = {
        "name": PROFILE["name"],
        "project_list": Project.objects.all(),
    }
    return render(request, "projects.html", context)


def show_project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    context = {
        "name": PROFILE["name"],
        "project": project,
    }
    return render(request, "project_detail.html", context)