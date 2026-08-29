from dataclasses import dataclass
from datetime import date, timedelta

from .models import Chore, Roommate, RotaSettings


@dataclass
class RotaItem:
    date: date
    chore: Chore
    roommate: Roommate


def monday_for(day):
    return day - timedelta(days=day.weekday())


def build_week(week_start):
    """Give every task in a week to that week's single alphabetical owner."""
    week_start = monday_for(week_start)
    roommates = list(Roommate.objects.filter(active=True).order_by("name"))
    chores = list(Chore.objects.filter(active=True).order_by("name"))
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


def week_owner(week_start, roommates=None):
    roommates = roommates or list(Roommate.objects.filter(active=True).order_by("name"))
    if not roommates:
        return None
    anchor = monday_for(RotaSettings.load().rotation_start)
    rotation = ((monday_for(week_start) - anchor).days // 7) % len(roommates)
    return roommates[rotation]
