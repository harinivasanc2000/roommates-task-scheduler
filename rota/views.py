from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Chore, Roommate, RotaSettings, TaskStatus, upcoming_monday
from .services import build_week, monday_for, week_owner


def _requested_week(request):
    try:
        return monday_for(date.fromisoformat(request.GET.get("week", "")))
    except ValueError:
        return upcoming_monday()


def schedule(request):
    week_start = _requested_week(request)
    rota_settings = RotaSettings.load()
    weeks = []
    all_items = []
    for week_offset in range(5):
        start = week_start + timedelta(days=week_offset * 7)
        all_items.extend(build_week(start))
    statuses = {
        (status.task_date, status.chore_id, status.roommate_id): status
        for status in TaskStatus.objects.filter(task_date__gte=week_start, task_date__lte=week_start + timedelta(days=34))
    }
    for item in all_items:
        item.status = statuses.get((item.date, item.chore.id, item.roommate.id))
        item.original_date = item.date
        item.completed = item.status.completed if item.status else False
        item.note = item.status.note if item.status else ""
        if item.status and item.status.scheduled_for:
            item.date = item.status.scheduled_for
    for week_offset in range(5):
        start = week_start + timedelta(days=week_offset * 7)
        week_items = [item for item in all_items if start <= item.date < start + timedelta(days=7)]
        days = []
        for offset in range(7):
            day = start + timedelta(days=offset)
            days.append({"date": day, "items": [item for item in week_items if item.date == day]})
        done = sum(item.completed for item in week_items)
        weeks.append({"start": start, "end": start + timedelta(days=6), "days": days,
                      "owner": week_owner(start), "done": done, "total": len(week_items),
                      "percent": round((done / len(week_items)) * 100) if week_items else 0})
    active_roommates = Roommate.objects.filter(active=True).order_by("name")
    selected_person = active_roommates.filter(pk=request.session.get("roommate_id")).first()
    return render(request, "rota/schedule.html", {
        "weeks": weeks,
        "week_start": week_start,
        "previous_week": week_start - timedelta(days=7),
        "next_week": week_start + timedelta(days=7),
        "roommates": Roommate.objects.order_by("name"),
        "chores": Chore.objects.order_by("name"),
        "rotation_start": rota_settings.rotation_start,
        "rota_settings": rota_settings,
        "selected_person": selected_person,
        "needs_identity": selected_person is None,
    })


@require_POST
def choose_person(request):
    person = Roommate.objects.filter(pk=request.POST.get("roommate_id"), active=True).first()
    if not person:
        return HttpResponseBadRequest("Choose an active roommate")
    request.session["roommate_id"] = person.id
    return redirect(request.POST.get("next", "/"))


@require_POST
def update_task(request):
    try:
        task_date = date.fromisoformat(request.POST["task_date"])
        chore = Chore.objects.get(pk=request.POST["chore_id"])
        roommate = Roommate.objects.get(pk=request.POST["roommate_id"])
    except (KeyError, ValueError, Chore.DoesNotExist, Roommate.DoesNotExist):
        return HttpResponseBadRequest("Unknown task")
    status, _ = TaskStatus.objects.get_or_create(task_date=task_date, chore=chore, roommate=roommate)
    if "completed" in request.POST:
        status.completed = request.POST["completed"] == "true"
    if "note" in request.POST:
        status.note = request.POST["note"].strip()
    if "scheduled_for" in request.POST:
        scheduled_for = date.fromisoformat(request.POST["scheduled_for"])
        week_start = monday_for(task_date)
        if not week_start <= scheduled_for <= week_start + timedelta(days=6):
            return HttpResponseBadRequest("A task can only be moved within its assigned week")
        status.scheduled_for = scheduled_for
    status.save()
    return redirect(request.POST.get("next", "/"))


@require_POST
def household_settings(request):
    action = request.POST.get("action")
    if action == "add_roommate":
        name = request.POST.get("name", "").strip()
        if name:
            profiles = {
                "hari": ("🐶", "Woof woof, Hari! Ready to make this week pawsome?"),
                "huanlin": ("🦁", "欢迎回来，Huanlin！今天也一起把家里照顾好吧。"),
                "hualin": ("🦁", "欢迎回来，Hualin！今天也一起把家里照顾好吧。"),
                "jaclyn": ("🦘", "G’day, Jaclyn! Let’s get this place looking bonzer."),
                "tanith": ("🐱", "Howzit, Tanith! Cooper says you’ve got this."),
            }
            avatar, greeting = profiles.get(name.lower(), ("🙂", f"Welcome back, {name}!"))
            Roommate.objects.get_or_create(name=name, defaults={
                "email": request.POST.get("email", "").strip(), "avatar": avatar, "greeting": greeting,
            })
    elif action == "add_chore":
        name = request.POST.get("name", "").strip()
        if name:
            Chore.objects.get_or_create(name=name, defaults={
                "frequency": request.POST.get("frequency", Chore.Frequency.WEEKLY),
                "weekday": int(request.POST.get("weekday", 0)),
            })
    elif action == "toggle_roommate":
        Roommate.objects.filter(pk=request.POST.get("id")).update(active=request.POST.get("active") == "true")
    elif action == "toggle_chore":
        Chore.objects.filter(pk=request.POST.get("id")).update(active=request.POST.get("active") == "true")
    elif action == "update_rotation":
        try:
            rotation_start = monday_for(date.fromisoformat(request.POST["rotation_start"]))
            starting_roommate = Roommate.objects.get(pk=request.POST["starting_roommate"], active=True)
        except (KeyError, ValueError, Roommate.DoesNotExist):
            return HttpResponseBadRequest("Choose a valid date and active roommate")
        settings = RotaSettings.load()
        settings.rotation_start = rotation_start
        settings.starting_roommate = starting_roommate
        settings.save(update_fields=["rotation_start", "starting_roommate"])
    return redirect(request.POST.get("next", "/"))


def calendar_download(request):
    week_start = _requested_week(request)
    person_id = request.GET.get("person") or request.session.get("roommate_id")
    person = Roommate.objects.filter(pk=person_id, active=True).first()
    if not person:
        return HttpResponseBadRequest("Choose who you are before downloading a calendar")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Roommate Rota//EN", "CALSCALE:GREGORIAN"]
    stamp = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    items = [item for start in (week_start + timedelta(days=7 * n) for n in range(5))
             for item in build_week(start) if item.roommate.id == person.id]
    statuses = {(status.task_date, status.chore_id, status.roommate_id): status for status in
                TaskStatus.objects.filter(task_date__gte=week_start, task_date__lte=week_start + timedelta(days=34))}
    for index, item in enumerate(items):
        status = statuses.get((item.date, item.chore.id, item.roommate.id))
        event_date = status.scheduled_for if status and status.scheduled_for else item.date
        day = event_date.strftime("%Y%m%d")
        next_day = (event_date + timedelta(days=1)).strftime("%Y%m%d")
        summary = f"{item.chore.name} — {item.roommate.name}".replace(",", "\\,")
        lines += [
            "BEGIN:VEVENT", f"UID:{day}-{index}@roommate-rota", f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{day}", f"DTEND;VALUE=DATE:{next_day}",
            f"SUMMARY:{summary}", "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    response = HttpResponse("\r\n".join(lines) + "\r\n", content_type="text/calendar; charset=utf-8")
    safe_name = "".join(character for character in person.name.lower() if character.isalnum())
    response["Content-Disposition"] = f'attachment; filename="{safe_name}-rota-{week_start}.ics"'
    return response
