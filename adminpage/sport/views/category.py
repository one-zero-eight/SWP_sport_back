from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.decorators import permission_classes

from api.crud import get_sports, get_clubs, get_sc_training_group


@login_required
def category_view(request, **kwargs):
    student = getattr(request.user, "student", None)
    sports = get_sports(student=student)
    clubs = sorted(
        [{
            "available_places": club["capacity"] - club["current_load"],
            **club,
        }
            for club in get_clubs(student=student)],
        key=lambda group: (group["current_load"] >= group["capacity"], group["name"])
    )
    sc_training_group_id = get_sc_training_group()["id"]
    return render(request, "category.html", {
        "sports": sports,
        "clubs": clubs,
        "sc_training_group_id": sc_training_group_id,
    })
