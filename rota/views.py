from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import CelebrationCounter, Chore, Roommate, RotaSettings, RotaSwap, TaskStatus, upcoming_monday
from .celebrations import celebration_for
from .services import build_week, monday_for, week_owner


def _requested_week(request):
    try:
        return monday_for(date.fromisoformat(request.GET.get("week", "")))
    except ValueError:
        return upcoming_monday()


def schedule(request):
    week_start = _requested_week(request)
    rota_settings = RotaSettings.load()
    active_roommates = Roommate.objects.filter(active=True).order_by("name")
    selected_person = active_roommates.filter(pk=request.session.get("roommate_id")).first()
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
        owner = week_owner(start)
        weeks.append({"start": start, "end": start + timedelta(days=6), "days": days,
                      "owner": owner, "is_mine": bool(selected_person and owner == selected_person),
                      "done": done, "total": len(week_items),
                      "percent": round((done / len(week_items)) * 100) if week_items else 0})
    personal_week = next((week for week in weeks if week["is_mine"]), None)
    personal_items = sorted(
        (item for item in all_items if selected_person and item.roommate == selected_person and not item.completed),
        key=lambda item: (item.date, item.chore.name),
    )
    today = date.today()
    next_task = next((item for item in personal_items if item.date >= today), None)
    if next_task is None and personal_items:
        next_task = personal_items[0]
    incoming_swaps = RotaSwap.objects.none()
    sent_swaps = RotaSwap.objects.none()
    if selected_person:
        incoming_swaps = RotaSwap.objects.filter(requested_with=selected_person, status=RotaSwap.Status.PENDING)
        sent_swaps = RotaSwap.objects.filter(requested_by=selected_person)[:3]
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
        "personal_week": personal_week,
        "next_task": next_task,
        "remaining_personal_tasks": len(personal_items),
        "incoming_swaps": incoming_swaps,
        "sent_swaps": sent_swaps,
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
    selected_person = Roommate.objects.filter(pk=request.session.get("roommate_id"), active=True).first()
    if not selected_person or selected_person != roommate:
        return HttpResponseForbidden("You can only change tasks assigned to you")
    valid_task = any(item.date == task_date and item.chore.id == chore.id and item.roommate == roommate
                     for item in build_week(monday_for(task_date)))
    if not valid_task:
        return HttpResponseBadRequest("This task is not part of the current rota")
    status, _ = TaskStatus.objects.get_or_create(task_date=task_date, chore=chore, roommate=roommate)
    if "completed" in request.POST:
        marking_complete = request.POST["completed"] == "true"
        if marking_complete and not status.completed:
            counter, _ = CelebrationCounter.objects.get_or_create(roommate=roommate, chore=chore)
            counter.count += 1
            counter.save(update_fields=["count"])
            messages.success(request, celebration_for(roommate, chore, counter.count))
        status.completed = marking_complete
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
def request_swap(request):
    selected_person = Roommate.objects.filter(pk=request.session.get("roommate_id"), active=True).first()
    if not selected_person:
        return HttpResponseForbidden("Choose who you are first")
    try:
        requester_week = monday_for(date.fromisoformat(request.POST["requester_week"]))
        requested_with = Roommate.objects.get(pk=request.POST["requested_with"], active=True)
    except (KeyError, ValueError, Roommate.DoesNotExist):
        return HttpResponseBadRequest("Choose a valid roommate and week")
    if requested_with == selected_person or week_owner(requester_week) != selected_person:
        return HttpResponseForbidden("You can only swap your own week")
    requested_week = next(
        (requester_week + timedelta(weeks=offset) for offset in range(1, 9)
         if week_owner(requester_week + timedelta(weeks=offset)) == requested_with), None
    )
    if not requested_week:
        return HttpResponseBadRequest("No upcoming week was found for that roommate")
    conflict = RotaSwap.objects.filter(status__in=[RotaSwap.Status.PENDING, RotaSwap.Status.ACCEPTED]).filter(
        Q(requester_week__in=[requester_week, requested_week]) |
        Q(requested_week__in=[requester_week, requested_week])
    ).exists()
    if not conflict:
        RotaSwap.objects.create(requested_by=selected_person, requested_with=requested_with,
                                requester_week=requester_week, requested_week=requested_week)
    return redirect(request.POST.get("next", "/"))


@require_POST
def respond_swap(request, swap_id):
    selected_person = Roommate.objects.filter(pk=request.session.get("roommate_id"), active=True).first()
    swap = RotaSwap.objects.filter(pk=swap_id, status=RotaSwap.Status.PENDING).first()
    if not selected_person or not swap or swap.requested_with != selected_person:
        return HttpResponseForbidden("Only the requested roommate can answer this swap")
    decision = request.POST.get("decision")
    if decision not in {RotaSwap.Status.ACCEPTED, RotaSwap.Status.DECLINED}:
        return HttpResponseBadRequest("Choose accept or decline")
    if decision == RotaSwap.Status.ACCEPTED:
        overlap = RotaSwap.objects.filter(status=RotaSwap.Status.ACCEPTED).filter(
            Q(requester_week__in=[swap.requester_week, swap.requested_week]) |
            Q(requested_week__in=[swap.requester_week, swap.requested_week])
        ).exists()
        if overlap:
            return HttpResponseBadRequest("One of these weeks has already been swapped")
    swap.status = decision
    swap.responded_at = timezone.now()
    swap.save(update_fields=["status", "responded_at"])
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
    person_id = request.session.get("roommate_id")
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
