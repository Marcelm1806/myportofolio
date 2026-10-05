from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST, require_safe
from django.views.decorators.vary import vary_on_cookie

from main.forms import EducationForm, ProjectForm
from main.models import Education, Experience, Project
from main.permissions import (
    can_edit_education,
    can_manage_education,
    education_access_context,
)


PROFILE = {
    "name": "Marcel Mikula",
    "npm": "2606816592",
    "study_program": "Business Information Systems",
    "bio": (
        "A Business Information Systems student from Germany, "
        "currently completing an exchange semester at Universitas Indonesia."
    ),
}


@require_http_methods(["GET", "POST"])
def register(request):
    form = UserCreationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created successfully. Please log in.")
        return redirect("main:login")
    return render(request, "register.html", {"name": PROFILE["name"], "form": form})


@require_http_methods(["GET", "POST"])
def login_user(request):
    form = AuthenticationForm(
        request, data=request.POST if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        # As in Tutorial 4, login always returns to the profile page.
        response = redirect("main:show_main")
        response.set_cookie(
            "last_login",
            timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
        )
        return response
    return render(request, "login.html", {"name": PROFILE["name"], "form": form})


@require_POST
def logout_user(request):
    """The navbar submits a CSRF-protected POST rather than changing state on GET."""
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie("last_login", samesite="Lax")
    return response


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
        "last_login": (
            request.COOKIES.get("last_login")
            or "No active login session / Cookie not found"
        ),
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
    projects = Project.objects.prefetch_related("starred_by")
    title_query = request.GET.get("title", "").strip()
    if title_query:
        projects = projects.filter(title__icontains=title_query)
    return projects


@require_safe
@vary_on_cookie
def get_projects_json(request):
    # A custom JSON representation can include state belonging to this session.
    # prefetch_related in _filtered_projects avoids a query per card.
    data = []
    user_id = request.user.pk if request.user.is_authenticated else None
    for project in _filtered_projects(request):
        supporters = list(project.starred_by.all())
        fields = {
            name: getattr(project, name)
            for name in ProjectForm.Meta.fields
        }
        fields.update({
            "technology_list": project.technology_list,
            "star_count": len(supporters),
            "is_starred": any(user.pk == user_id for user in supporters),
            "starred_by_names": ", ".join(user.username for user in supporters),
            # Preserve Tutorial 4's public username-only relation format.
            "starred_by": [[user.username] for user in supporters],
        })
        data.append({
            "model": "main.project",
            "pk": str(project.pk),
            "fields": fields,
            "urls": {
                "detail": reverse("main:show_project_detail", args=[project.pk]),
                "star": reverse("main:toggle_star", args=[project.pk]),
                "delete": reverse("main:delete_project", args=[project.pk]),
            },
        })
    return JsonResponse(data, safe=False)


@require_safe
def get_projects_xml(request):
    data = serializers.serialize(
        "xml", _filtered_projects(request), use_natural_foreign_keys=True,
    )
    return HttpResponse(data, content_type="application/xml")


@require_safe
def show_projects(request):
    # Tutorial 5: the browser requests the records separately with fetch().
    title_query = request.GET.get("title", "").strip()
    context = {
        "name": PROFILE["name"],
        "title_query": title_query,
        "form": ProjectForm(),
        "project_config": {
            "jsonUrl": reverse("main:get_projects_json"),
            "createUrl": reverse("main:create_project_ajax"),
            "csrfToken": get_token(request),
            "isSuperuser": request.user.is_superuser,
            "initialQuery": title_query,
        },
    }
    return render(request, "projects.html", context)


@login_required(login_url="main:login")
@require_http_methods(["GET", "POST"])
def create_project(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    # An empty POST must still be a bound form so required-field errors appear.
    form = ProjectForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project added successfully.")
        return redirect("main:show_projects")

    context = {"name": PROFILE["name"], "form": form}
    return render(request, "projects_form.html", context)


@require_POST
def create_project_ajax(request):
    # JSON clients need an explicit 403, not a redirect to an HTML login page.
    if not request.user.is_superuser:
        return JsonResponse({"message": "Only the portfolio owner can add projects."}, status=403)
    form = ProjectForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    project = form.save()
    return JsonResponse({
        "message": "Project added successfully.", "pk": str(project.pk),
    }, status=201)


@login_required(login_url="main:login")
@require_POST
def delete_project(request, project_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    project = get_object_or_404(Project, pk=project_id)
    project.delete()
    messages.success(request, "Project deleted successfully.")
    return redirect("main:show_projects")


@login_required(login_url="main:login")
@require_POST
def toggle_star(request, project_id):
    """Toggle only the current account's membership, never a submitted user ID."""
    project = get_object_or_404(Project, pk=project_id)
    if project.starred_by.filter(pk=request.user.pk).exists():
        project.starred_by.remove(request.user)
    else:
        project.starred_by.add(request.user)
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
    entries = _education_with_star_state(Education.objects.all(), request.user)
    query, status = _education_filters(request)
    if query:
        entries = entries.filter(
            Q(institution__icontains=query) | Q(degree__icontains=query),
        )
    if status:
        entries = entries.filter(is_current=(status == "current"))
    if request.GET.get("starred") == "1":
        # The filter always belongs to the session account, never a supplied ID.
        entries = (
            entries.filter(is_starred=True)
            if request.user.is_authenticated else entries.none()
        )
    return entries


def _education_json(entries):
    """Retain the serializer exercise for the server-rendered home overview."""
    return HttpResponse(
        serializers.serialize("json", entries, fields=(
            "institution", "degree", "description", "start_year", "end_year",
            "is_current", "website", "display_order", "created_at", "updated_at",
        )),
        content_type="application/json",
    )


@require_safe
@vary_on_cookie
def get_education_json(request):
    # Explicit allowlist: totals and the caller's boolean, never stargazer IDs.
    records = []
    for entry in _filtered_education(request):
        fields = {
            name: getattr(entry, name) for name in (
                "institution", "degree", "description", "start_year", "end_year",
                "is_current", "website", "display_order", "created_at", "updated_at",
            )
        }
        fields.update({
            "period_label": entry.period_label,
            "star_count": entry.star_count,
            "is_starred": entry.is_starred,
        })
        records.append({
            "model": "main.education", "pk": str(entry.pk), "fields": fields,
            "urls": {
                "detail": reverse("main:show_education_detail", args=[entry.pk]),
                "edit": reverse("main:update_education", args=[entry.pk]),
                "delete": reverse("main:delete_education", args=[entry.pk]),
                "star": reverse("main:toggle_education_star_ajax", args=[entry.pk]),
            },
        })
    return JsonResponse(records, safe=False)


def _education_with_star_state(entries, user):
    """Aggregate in one query; Exists keeps personal filtering independent of totals."""
    membership = Education.starred_by.through.objects.filter(
        education_id=OuterRef("pk"), user_id=user.pk,
    )
    own_star = (
        Exists(membership) if user.is_authenticated
        else Value(False, output_field=BooleanField())
    )
    return entries.annotate(
        star_count=Count("starred_by", distinct=True), is_starred=own_star,
    ).order_by(*Education._meta.ordering)


def _attach_education_star_state(entries, user):
    """Share the same computed state with the server-rendered detail page."""
    state = {
        row["pk"]: row
        for row in _education_with_star_state(
            Education.objects.filter(pk__in=[entry.pk for entry in entries]), user,
        )
        .values("pk", "star_count", "is_starred")
    }
    for entry in entries:
        values = state.get(entry.pk, {})
        entry.star_count = values.get("star_count", 0)
        entry.is_starred = values.get("is_starred", False)


@require_safe
def show_education(request):
    # Only a page skeleton; the browser requests records from the JSON endpoint.
    query, status = _education_filters(request)
    access = education_access_context(request.user)
    context = {
        "name": PROFILE["name"],
        "form": EducationForm(),
        "query": query,
        "status_filter": status,
        "starred_only": request.GET.get("starred") == "1",
        **access,
        "education_config": {
            "jsonUrl": reverse("main:get_education_json"),
            "createUrl": reverse("main:create_education_ajax"),
            "loginUrl": reverse("main:login"),
            "csrfToken": get_token(request),
            "isAuthenticated": request.user.is_authenticated,
            "canManage": access["can_manage_education"],
            "canEdit": access["can_edit_education"],
            "initialFilters": {
                "q": query, "status": status,
                "starred": "1" if request.GET.get("starred") == "1" else "",
            },
        },
    }
    return render(request, "education.html", context)


@require_safe
def show_education_detail(request, education_id):
    entry = get_object_or_404(Education, pk=education_id)
    _attach_education_star_state([entry], request.user)
    return render(request, "education_detail.html", {
        "name": PROFILE["name"],
        "education": entry,
        **education_access_context(request.user),
    })


@require_POST
def create_education_ajax(request):
    """Owner-only AJAX creation; invalid data never reaches save()."""
    if not can_manage_education(request.user):
        return JsonResponse({"message": "Only the owner can add education entries."}, status=403)
    form = EducationForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    entry = form.save()
    return JsonResponse({
        "pk": str(entry.pk), "message": "Education entry added successfully.",
    }, status=201)


@require_POST
def toggle_education_star_ajax(request, education_id):
    """Extra interaction: update a personal star without leaving the list."""
    if not request.user.is_authenticated:
        return JsonResponse({"message": "Please log in to star an education entry."}, status=403)
    entry = Education.objects.filter(pk=education_id).first()
    if entry is None:
        return JsonResponse({"message": "This education entry no longer exists."}, status=404)
    if entry.starred_by.filter(pk=request.user.pk).exists():
        entry.starred_by.remove(request.user)
        starred = False
    else:
        entry.starred_by.add(request.user)
        starred = True
    return JsonResponse({
        "pk": str(entry.pk), "is_starred": starred,
        "star_count": entry.starred_by.count(),
        "message": "Star added." if starred else "Star removed.",
    })


@login_required(login_url="main:login")
@require_POST
def toggle_education_star(request, education_id):
    """Change only the caller's star and preserve the current education filter."""
    entry = get_object_or_404(Education, pk=education_id)
    if entry.starred_by.filter(pk=request.user.pk).exists():
        entry.starred_by.remove(request.user)
        action = "removed"
    else:
        entry.starred_by.add(request.user)
        action = "added"
    messages.success(request, f"Star {action}: {entry.institution}.")

    # Construct local destinations ourselves; never trust an arbitrary next URL.
    if request.POST.get("return_to") == "detail":
        return redirect("main:show_education_detail", education_id=entry.pk)
    filters = {}
    query = request.POST.get("q", "").strip()
    status = request.POST.get("status", "")
    if query:
        filters["q"] = query
    if status in {"current", "completed"}:
        filters["status"] = status
    if request.POST.get("starred") == "1":
        filters["starred"] = "1"
    destination = reverse("main:show_education")
    if filters:
        destination += "?" + urlencode(filters)
    return redirect(destination)


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


@login_required(login_url="main:login")
@require_http_methods(["GET", "POST"])
def create_education(request):
    if not can_manage_education(request.user):
        raise PermissionDenied
    return _education_form_response(request)


@login_required(login_url="main:login")
@require_http_methods(["GET", "POST"])
def update_education(request, education_id):
    if not can_edit_education(request.user):
        raise PermissionDenied
    entry = get_object_or_404(Education, pk=education_id)
    return _education_form_response(request, instance=entry)


@login_required(login_url="main:login")
@require_POST
def delete_education(request, education_id):
    if not can_manage_education(request.user):
        raise PermissionDenied
    entry = get_object_or_404(Education, pk=education_id)
    entry.delete()
    messages.success(request, "Education entry deleted successfully.")
    return redirect("main:show_education")
