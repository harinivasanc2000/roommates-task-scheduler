from django.contrib import admin
from .models import Chore, Roommate


@admin.register(Roommate)
class RoommateAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "active")
    list_editable = ("active",)
    search_fields = ("name", "email")


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ("name", "frequency", "weekday", "active")
    list_editable = ("frequency", "weekday", "active")
    list_filter = ("frequency", "active")
