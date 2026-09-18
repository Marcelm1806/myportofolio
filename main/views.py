from django.contrib import messages
from django.core import serializers
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from main.forms import EducationForm, ProjectForm
from main.models import Education, Experience, Project


PROFILE = {
    "name": "Marcel Mikula",
    "npm": "2606816592",
    "study_program": "Business Information Systems",
    "bio": (
        "A Business Information Systems student from Germany, "
        "currently completing an exchange semester at Universitas Indonesia."
    ),
}


def _objects_from_json(response):
    """Deserialize for display only; never save objects supplied by this helper."""
    return [
        item.object
        for item in serializers.deserialize("json", response.content.decode("utf-8"))
    ]


@require_safe
def show_main(request):
    context = {
        **PROFILE,
        "education_list": _objects_from_json(_education_json(Education.objects.all())),
    }
    return render(request, "index.html", context)


@require_safe
def get_experience_json(request):
    experiences = Experience.objects.order_by("-started_at", "id")
    return HttpResponse(
        serializers.serialize("json", experiences), content_type="application/json",
    )


@require_safe
def show_experience(request):
    context = {
        "name": PROFILE["name"],
        "experience_list": _objects_from_json(get_experience_json(request)),
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
    project_list = _objects_from_json(response)
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


def _education_filters(request):
    """Normalize query parameters once for the HTML page and JSON endpoint."""
    status = request.GET.get("status", "")
    if status not in {"current", "completed"}:
        status = ""
    return request.GET.get("q", "").strip(), status


def _filtered_education(request):
    entries = Education.objects.all()
    query, status = _education_filters(request)
    if query:
        entries = entries.filter(
            Q(institution__icontains=query) | Q(degree__icontains=query),
        )
    if status:
        entries = entries.filter(is_current=(status == "current"))
    return entries


def _education_json(entries):
    """One serializer for the API, filtered page, and unfiltered home preview."""
    return HttpResponse(
        serializers.serialize("json", entries), content_type="application/json",
    )


@require_safe
def get_education_json(request):
    return _education_json(_filtered_education(request))


@require_safe
def show_education(request):
    # Call the JSON view directly, following Tutorial 3, without an HTTP loop.
    entries = _objects_from_json(get_education_json(request))
    query, status = _education_filters(request)
    context = {
        "name": PROFILE["name"],
        "education_list": entries,
        "query": query,
        "status_filter": status,
    }
    return render(request, "education.html", context)


def _education_form_response(request, *, instance=None):
    """Keep create/update validation identical; instance makes save() update."""
    is_update = instance is not None
    form = EducationForm(
        request.POST if request.method == "POST" else None,
        instance=instance,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        action = "updated" if is_update else "added"
        messages.success(request, f"Education entry {action} successfully.")
        return redirect("main:show_education")
    context = {
        "name": PROFILE["name"],
        "form": form,
        "education": instance,
        "is_update": is_update,
    }
    return render(request, "education_form.html", context)


@require_http_methods(["GET", "POST"])
def create_education(request):
    return _education_form_response(request)


@require_http_methods(["GET", "POST"])
def update_education(request, education_id):
    entry = get_object_or_404(Education, pk=education_id)
    return _education_form_response(request, instance=entry)


@require_POST
def delete_education(request, education_id):
    entry = get_object_or_404(Education, pk=education_id)
    entry.delete()
    messages.success(request, "Education entry deleted successfully.")
    return redirect("main:show_education")
