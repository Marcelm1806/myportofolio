from django.urls import path

from main.views import (
    create_project,
    delete_project,
    get_projects_json,
    get_projects_xml,
    show_experience,
    show_main,
    show_project_detail,
    show_projects,
)


app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("projects/", show_projects, name="show_projects"),
    path("projects/add/", create_project, name="create_project"),
    path("api/projects/", get_projects_json, name="get_projects_json"),
    path("api/projects/xml/", get_projects_xml, name="get_projects_xml"),
    path(
        "projects/<uuid:project_id>/delete/",
        delete_project,
        name="delete_project",
    ),
    path(
        "projects/<uuid:project_id>/",
        show_project_detail,
        name="show_project_detail",
    ),
]
