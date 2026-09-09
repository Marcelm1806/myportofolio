from django.shortcuts import render

from main.models import Experience


def show_main(request):
    context = {
        "name": "Marcel Mikula",
        "npm": "2606816592",
        "study_program": "Business Information Systems",
        "bio": (
            "A Business Information System student form germany doing his exchange semester at Universitas Indonesia. "
        ),
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Marcel Mikula",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)