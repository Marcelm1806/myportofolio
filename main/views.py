from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from main.forms import ProjectForm
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


def _filtered_projects(request):
    """Share the title filter between the JSON and XML representations."""
    projects = Project.objects.all()
    title_query = request.GET.get("title", "").strip()
    if title_query:
        projects = projects.filter(title__icontains=title_query)
    return projects


@require_safe
def get_projects_json(request):
    data = serializers.serialize("json", _filtered_projects(request))
    return HttpResponse(data, content_type="application/json")


@require_safe
def get_projects_xml(request):
    data = serializers.serialize("xml", _filtered_projects(request))
    return HttpResponse(data, content_type="application/xml")


@require_safe
def show_projects(request):
    # Tutorial 3: demonstrate serialization and deserialization explicitly.
    # This is a Python function call, not an HTTP request to our own server.
    response = get_projects_json(request)
    project_list = [
        item.object
        for item in serializers.deserialize("json", response.content.decode("utf-8"))
    ]
    context = {
        "name": PROFILE["name"],
        "project_list": project_list,
        "title_query": request.GET.get("title", "").strip(),
    }
    return render(request, "projects.html", context)


@require_http_methods(["GET", "POST"])
def create_project(request):
    # An empty POST must still be a bound form so required-field errors appear.
    form = ProjectForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project added successfully.")
        return redirect("main:show_projects")

    context = {"name": PROFILE["name"], "form": form}
    return render(request, "projects_form.html", context)


@require_POST
def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    project.delete()
    messages.success(request, "Project deleted successfully.")
    return redirect("main:show_projects")


def show_project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    context = {
        "name": PROFILE["name"],
        "project": project,
    }
    return render(request, "project_detail.html", context)
