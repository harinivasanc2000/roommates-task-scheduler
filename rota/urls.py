from django.urls import path
from . import views

app_name = "rota"
urlpatterns = [
    path("", views.schedule, name="schedule"),
    path("calendar.ics", views.calendar_download, name="calendar"),
    path("task/", views.update_task, name="update_task"),
    path("household/", views.household_settings, name="household"),
    path("choose-person/", views.choose_person, name="choose_person"),
    path("swap/request/", views.request_swap, name="request_swap"),
    path("swap/<int:swap_id>/respond/", views.respond_swap, name="respond_swap"),
    path("notes/", views.household_note, name="household_note"),
]
