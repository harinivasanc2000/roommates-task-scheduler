from dataclasses import dataclass
from datetime import date, timedelta

from django.db import models
from django.db.models import Count, Q
from django.utils import timezone

from .models import CelebrationCounter, Chore, Roommate, RotaSettings, RotaSwap, TaskStatus


@dataclass
class RotaItem:
    date: date
    chore: Chore
    roommate: Roommate


def monday_for(day):
    return day - timedelta(days=day.weekday())


def available_roommates(as_of=None):
    """Active roommates who are not away on the given date (default: today)."""
    as_of = as_of or date.today()
    people = list(Roommate.objects.filter(active=True).order_by("name"))
    return [p for p in people if not p.away_until or p.away_until < as_of]


def build_week(week_start):
    """Give every task in a week to that week's single alphabetical owner."""
    week_start = monday_for(week_start)
    roommates = available_roommates(week_start)
    chores = list(Chore.objects.filter(active=True).order_by("name"))
    if not roommates:
        # Fall back to all active so the calendar still renders when everyone is away.
        roommates = list(Roommate.objects.filter(active=True).order_by("name"))
    if not roommates:
        return []

    owner = week_owner(week_start, roommates)
    items = []
    for chore in chores:
        if chore.frequency == Chore.Frequency.ALTERNATE_DAYS:
            days = range(0, 7, 2)  # Monday, Wednesday, Friday, Sunday
        else:
            days = [chore.weekday]
        for day_offset in days:
            items.append(RotaItem(week_start + timedelta(days=day_offset), chore, owner))
    return sorted(items, key=lambda item: (item.date, item.chore.name))


def base_week_owner(week_start, roommates=None):
    roommates = roommates if roommates is not None else available_roommates(week_start)
    if not roommates:
        roommates = list(Roommate.objects.filter(active=True).order_by("name"))
    if not roommates:
        return None
    settings = RotaSettings.load()
    anchor = monday_for(settings.rotation_start)
    try:
        starting_index = next(
            index for index, person in enumerate(roommates)
            if person.id == settings.starting_roommate_id
        )
    except StopIteration:
        starting_index = 0
    rotation = (starting_index + ((monday_for(week_start) - anchor).days // 7)) % len(roommates)
    return roommates[rotation]


def week_owner(week_start, roommates=None):
    week_start = monday_for(week_start)
    swap = RotaSwap.objects.filter(status=RotaSwap.Status.ACCEPTED).filter(
        models.Q(requester_week=week_start) | models.Q(requested_week=week_start)
    ).first()
    if swap:
        return swap.requested_with if swap.requester_week == week_start else swap.requested_by
    return base_week_owner(week_start, roommates)


def personal_stats(person, all_items, statuses, today=None):
    """This-week progress, lifetime completions, and simple day streak for a roommate."""
    today = today or date.today()
    week_start = monday_for(today)
    week_end = week_start + timedelta(days=6)
    personal = [i for i in all_items if i.roommate == person]
    week_items = [i for i in personal if week_start <= i.date <= week_end]
    week_done = sum(1 for i in week_items if i.completed)
    lifetime = (
        CelebrationCounter.objects.filter(roommate=person).aggregate(total=models.Sum("count"))["total"]
        or 0
    )
    # Streak: consecutive days (looking back from today) with at least one completion.
    completed_dates = set(
        TaskStatus.objects.filter(roommate=person, completed=True)
        .values_list("task_date", flat=True)
    )
    # Also count rescheduled completions on scheduled_for when present.
    for status in TaskStatus.objects.filter(roommate=person, completed=True).exclude(scheduled_for=None):
        completed_dates.add(status.scheduled_for)
    streak = 0
    cursor = today
    while cursor in completed_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return {
        "week_done": week_done,
        "week_total": len(week_items),
        "week_percent": round((week_done / len(week_items)) * 100) if week_items else 0,
        "lifetime": lifetime,
        "streak": streak,
    }


def fairness_board(weeks_back=4):
    """Completions per active roommate over the last N weeks."""
    today = date.today()
    since = monday_for(today) - timedelta(weeks=weeks_back)
    counts = {
        row["roommate_id"]: row["n"]
        for row in TaskStatus.objects.filter(completed=True, task_date__gte=since)
        .values("roommate_id")
        .annotate(n=Count("id"))
    }
    board = []
    for person in Roommate.objects.filter(active=True).order_by("name"):
        board.append({
            "person": person,
            "completions": counts.get(person.id, 0),
            "away": bool(person.away_until and person.away_until >= today),
        })
    board.sort(key=lambda row: (-row["completions"], row["person"].name))
    return board


def recent_activity(limit=8):
    """Latest completed tasks or notes for a lightweight household feed."""
    qs = (
        TaskStatus.objects.select_related("chore", "roommate")
        .filter(Q(completed=True) | ~Q(note=""))
        .order_by("-updated_at")[:limit]
    )
    feed = []
    for status in qs:
        when = status.scheduled_for or status.task_date
        if status.completed:
            text = f"completed {status.chore.name}"
        else:
            text = f"left a note on {status.chore.name}"
        feed.append({
            "person": status.roommate,
            "text": text,
            "note": status.note,
            "when": when,
            "updated_at": status.updated_at,
        })
    return feed
