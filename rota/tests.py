from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from .models import Chore, Roommate, RotaSettings, TaskStatus
from .services import build_week, week_owner


class RotaTests(TestCase):
    def setUp(self):
        Roommate.objects.all().delete()
        Roommate.objects.create(name="Zara")
        Roommate.objects.create(name="Alex")
        RotaSettings.objects.update_or_create(pk=1, defaults={
            "rotation_start": date(2026, 8, 24), "starting_roommate": None,
        })

    def test_week_is_monday_to_sunday_and_trash_is_alternate_days(self):
        items = build_week(date(2026, 8, 26))
        trash = [item for item in items if item.chore.frequency == Chore.Frequency.ALTERNATE_DAYS]
        self.assertEqual([item.date.weekday() for item in trash], [0, 2, 4, 6])
        self.assertEqual({item.roommate.name for item in items}, {"Alex"})
        self.assertEqual(week_owner(date(2026, 8, 31)).name, "Zara")

    def test_four_people_take_one_complete_week_each_alphabetically(self):
        Roommate.objects.create(name="Maya")
        Roommate.objects.create(name="Ben")
        owners = [week_owner(date(2026, 8, 24) + timedelta(weeks=offset)).name for offset in range(4)]
        self.assertEqual(owners, ["Alex", "Ben", "Maya", "Zara"])

    def test_rotation_start_can_be_changed_from_the_website(self):
        hari = Roommate.objects.create(name="Hari")
        huanlin = Roommate.objects.create(name="Huanlin")
        response = self.client.post(reverse("rota:household"), {
            "action": "update_rotation", "rotation_start": "2026-08-31",
            "starting_roommate": huanlin.id,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(week_owner(date(2026, 8, 24)), hari)
        self.assertEqual(week_owner(date(2026, 8, 31)), huanlin)

    def test_page_and_calendar_download(self):
        response = self.client.get(reverse("rota:schedule"), {"week": "2026-08-24"})
        self.assertContains(response, "Next 5 weeks")
        self.assertContains(response, "Change the look")
        self.assertContains(response, "Continue without choosing")
        alex = Roommate.objects.get(name="Alex")
        calendar = self.client.get(reverse("rota:calendar"), {"week": "2026-08-24", "person": alex.id})
        self.assertEqual(calendar["Content-Type"], "text/calendar; charset=utf-8")
        self.assertIn(b"BEGIN:VCALENDAR", calendar.content)
        self.assertIn(b"Alex", calendar.content)
        self.assertNotIn(b"Zara", calendar.content)

    def test_identity_choice_is_remembered(self):
        alex = Roommate.objects.get(name="Alex")
        response = self.client.post(reverse("rota:choose_person"), {"roommate_id": alex.id})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["roommate_id"], alex.id)
        self.assertContains(self.client.get(reverse("rota:schedule")), "HELLO, ALEX")

    def test_anyone_can_record_task_completion_and_note(self):
        item = build_week(date(2026, 8, 24))[0]
        response = self.client.post(reverse("rota:update_task"), {
            "task_date": item.date.isoformat(), "chore_id": item.chore.id,
            "roommate_id": item.roommate.id, "completed": "true", "note": "Bin bags are under the sink.",
            "scheduled_for": "2026-08-26",
        })
        self.assertEqual(response.status_code, 302)
        status = TaskStatus.objects.get(task_date=item.date, chore=item.chore, roommate=item.roommate)
        self.assertTrue(status.completed)
        self.assertEqual(status.note, "Bin bags are under the sink.")
        self.assertEqual(status.scheduled_for, date(2026, 8, 26))
