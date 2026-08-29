from dataclasses import dataclass
from datetime import date, timedelta

from django.db import models

from .models import Chore, Roommate, RotaSettings, RotaSwap


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


def base_week_owner(week_start, roommates=None):
    roommates = roommates or list(Roommate.objects.filter(active=True).order_by("name"))
    if not roommates:
        return None
    settings = RotaSettings.load()
    anchor = monday_for(settings.rotation_start)
    try:
        starting_index = next(index for index, person in enumerate(roommates)
                              if person.id == settings.starting_roommate_id)
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
