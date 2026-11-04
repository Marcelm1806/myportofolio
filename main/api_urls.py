from django.urls import path

from main import api_views

app_name = "api"

urlpatterns = [
    path("projects/", api_views.project_list, name="project_list"),
    path("projects/<uuid:project_id>/", api_views.project_detail, name="project_detail"),
    path("projects/<uuid:project_id>/star/", api_views.toggle_project_star, name="toggle_project_star"),
    path("education/", api_views.education_list, name="education_list"),
    path("education/<uuid:education_id>/", api_views.education_detail, name="education_detail"),
    path("education/<uuid:education_id>/star/", api_views.toggle_education_star, name="toggle_education_star"),
]
