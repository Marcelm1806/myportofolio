from django.urls import path

from main.views import (
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
    path(
        "projects/<uuid:project_id>/",
        show_project_detail,
        name="show_project_detail",
    ),
]