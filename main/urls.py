from django.urls import path

from main.views import (
    create_education,
    create_project,
    delete_education,
    delete_project,
    get_education_json,
    get_experience_json,
    get_projects_json,
    get_projects_xml,
    show_experience,
    show_education,
    show_main,
    show_project_detail,
    show_projects,
    update_education,
)


app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("api/experience/", get_experience_json, name="get_experience_json"),
    path("education/", show_education, name="show_education"),
    path("education/add/", create_education, name="create_education"),
    path("api/education/", get_education_json, name="get_education_json"),
    path(
        "education/<uuid:education_id>/edit/",
        update_education,
        name="update_education",
    ),
    path(
        "education/<uuid:education_id>/delete/",
        delete_education,
        name="delete_education",
    ),
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
