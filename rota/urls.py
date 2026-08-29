from django.urls import path
from . import views

app_name = "rota"
urlpatterns = [
    path("", views.schedule, name="schedule"),
    path("calendar.ics", views.calendar_download, name="calendar"),
    path("task/", views.update_task, name="update_task"),
    path("household/", views.household_settings, name="household"),
    path("choose-person/", views.choose_person, name="choose_person"),
]
