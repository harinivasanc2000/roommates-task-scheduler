from datetime import date, timedelta

from django.db import models


def upcoming_monday():
    today = date.today()
    return today + timedelta(days=(-today.weekday()) % 7)


class RotaSettings(models.Model):
    rotation_start = models.DateField(default=upcoming_monday)
    starting_roommate = models.ForeignKey(
        "Roommate", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    @classmethod
    def load(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings


class Roommate(models.Model):
    name = models.CharField(max_length=80, unique=True)
    email = models.EmailField(blank=True)
    avatar = models.CharField(max_length=8, default="🙂")
    greeting = models.CharField(max_length=240, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Chore(models.Model):
    class Frequency(models.TextChoices):
        WEEKLY = "weekly", "Once a week"
        ALTERNATE_DAYS = "alternate_days", "Every other day"

    name = models.CharField(max_length=100, unique=True)
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.WEEKLY)
    weekday = models.PositiveSmallIntegerField(
        default=5,
        choices=[(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
                 (4, "Friday"), (5, "Saturday"), (6, "Sunday")],
        help_text="Day used for once-a-week chores.",
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaskStatus(models.Model):
    """Shared state for a generated rota task, kept separately from the rota rules."""
    task_date = models.DateField()
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE)
    roommate = models.ForeignKey(Roommate, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    note = models.TextField(blank=True)
    scheduled_for = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["task_date", "chore", "roommate"], name="one_task_status")]

    def __str__(self):
        return f"{self.chore} on {self.task_date}"


class RotaSwap(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    requested_by = models.ForeignKey(Roommate, on_delete=models.CASCADE, related_name="sent_swaps")
    requested_with = models.ForeignKey(Roommate, on_delete=models.CASCADE, related_name="received_swaps")
    requester_week = models.DateField()
    requested_week = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.requested_by} ↔ {self.requested_with} ({self.status})"


class CelebrationCounter(models.Model):
    roommate = models.ForeignKey(Roommate, on_delete=models.CASCADE)
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["roommate", "chore"], name="one_celebration_counter")]
