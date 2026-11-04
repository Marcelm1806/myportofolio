"""Tutorial 7: session-authenticated REST APIs, alongside the original routes."""

from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_cookie
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.models import Education, Project
from main.permissions import IsPortfolioOwnerOrEditorOrReadOnly, IsPortfolioOwnerOrReadOnly
from main.serializers import EducationSerializer, ProjectSerializer
from main.views import _education_with_star_state, _filtered_education, _filtered_projects


@never_cache
@vary_on_cookie
@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrReadOnly])
def project_list(request):
    if request.method in ("GET", "HEAD"):
        serializer = ProjectSerializer(_filtered_projects(request), many=True, context={"request": request})
        return Response(serializer.data)
    serializer = ProjectSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@never_cache
@vary_on_cookie
@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrReadOnly])
def project_detail(request, project_id):
    project = get_object_or_404(Project.objects.prefetch_related("starred_by"), pk=project_id)
    if request.method in ("GET", "HEAD"):
        return Response(ProjectSerializer(project, context={"request": request}).data)
    if request.method == "DELETE":
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = ProjectSerializer(
        project, data=request.data, partial=request.method == "PATCH", context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@never_cache
@vary_on_cookie
@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def toggle_project_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    _toggle_star(project, request.user)
    return Response(ProjectSerializer(project, context={"request": request}).data)


@never_cache
@vary_on_cookie
@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def education_list(request):
    if request.method in ("GET", "HEAD"):
        serializer = EducationSerializer(_filtered_education(request), many=True, context={"request": request})
        return Response(serializer.data)
    serializer = EducationSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@never_cache
@vary_on_cookie
@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def education_detail(request, education_id):
    entry = get_object_or_404(
        _education_with_star_state(Education.objects.all(), request.user), pk=education_id,
    )
    if request.method in ("GET", "HEAD"):
        return Response(EducationSerializer(entry, context={"request": request}).data)
    if request.method == "DELETE":
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = EducationSerializer(
        entry, data=request.data, partial=request.method == "PATCH", context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@never_cache
@vary_on_cookie
@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def toggle_education_star(request, education_id):
    entry = get_object_or_404(Education, pk=education_id)
    _toggle_star(entry, request.user)
    return Response(EducationSerializer(entry, context={"request": request}).data)


def _toggle_star(entry, user):
    # Ignore supplied user IDs: a session can change only its own membership.
    if entry.starred_by.filter(pk=user.pk).exists():
        entry.starred_by.remove(user)
    else:
        entry.starred_by.add(user)
