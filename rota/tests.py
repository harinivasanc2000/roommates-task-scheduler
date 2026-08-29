from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from .celebrations import CATALOGUE, celebration_for
from .models import CelebrationCounter, Chore, Roommate, RotaSettings, RotaSwap, TaskStatus
from .services import build_week, week_owner


class RotaTests(TestCase):
    def setUp(self):
        Roommate.objects.all().delete()
        Roommate.objects.create(name="Zara")
        Roommate.objects.create(name="Alex")
        RotaSettings.objects.update_or_create(pk=1, defaults={
            "rotation_start": date(2026, 8, 24), "starting_roommate": None,
        })

    def choose(self, person):
        return self.client.post(reverse("rota:choose_person"), {"roommate_id": person.id})

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
        self.choose(alex)
        calendar = self.client.get(reverse("rota:calendar"), {"week": "2026-08-24", "person": Roommate.objects.get(name="Zara").id})
        self.assertEqual(calendar["Content-Type"], "text/calendar; charset=utf-8")
        self.assertIn(b"BEGIN:VCALENDAR", calendar.content)
        self.assertIn(b"Alex", calendar.content)
        self.assertNotIn(b"Zara", calendar.content)

    def test_identity_choice_is_remembered(self):
        alex = Roommate.objects.get(name="Alex")
        response = self.choose(alex)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["roommate_id"], alex.id)
        self.assertContains(self.client.get(reverse("rota:schedule")), "HELLO, ALEX")

    def test_roommate_can_record_their_own_completion_and_note(self):
        item = build_week(date(2026, 8, 24))[0]
        self.choose(item.roommate)
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

    def test_roommate_cannot_change_another_persons_task(self):
        item = build_week(date(2026, 8, 24))[0]
        zara = Roommate.objects.get(name="Zara")
        self.choose(zara)
        response = self.client.post(reverse("rota:update_task"), {
            "task_date": item.date.isoformat(), "chore_id": item.chore.id,
            "roommate_id": item.roommate.id, "completed": "true",
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(TaskStatus.objects.exists())

    def test_completion_progress_does_not_carry_to_next_roommate(self):
        alex = Roommate.objects.get(name="Alex")
        item = build_week(date(2026, 8, 24))[0]
        self.choose(alex)
        self.client.post(reverse("rota:update_task"), {
            "task_date": item.date.isoformat(), "chore_id": item.chore.id,
            "roommate_id": alex.id, "completed": "true",
        })
        response = self.client.get(reverse("rota:schedule"), {"week": "2026-08-24"})
        self.assertGreater(response.context["weeks"][0]["percent"], 0)
        self.assertEqual(response.context["weeks"][1]["percent"], 0)
        self.assertContains(response, "Nice work, Alex!")
        self.assertContains(response, "Zara’s rota")
        self.assertContains(response, "Their tasks and progress are private to their view")

    def test_swap_requires_target_confirmation_and_exchanges_weeks(self):
        alex = Roommate.objects.get(name="Alex")
        zara = Roommate.objects.get(name="Zara")
        self.choose(alex)
        self.client.post(reverse("rota:request_swap"), {
            "requester_week": "2026-08-24", "requested_with": zara.id,
        })
        swap = RotaSwap.objects.get()
        self.assertEqual(swap.status, RotaSwap.Status.PENDING)
        self.assertEqual(week_owner(date(2026, 8, 24)), alex)
        self.choose(zara)
        response = self.client.get(reverse("rota:schedule"), {"week": "2026-08-24"})
        self.assertContains(response, "Rota swap requests")
        self.client.post(reverse("rota:respond_swap", args=[swap.id]), {"decision": "accepted"})
        self.assertEqual(week_owner(date(2026, 8, 24)), zara)
        self.assertEqual(week_owner(date(2026, 8, 31)), alex)

    def test_every_housemate_has_three_distinct_messages_for_every_chore(self):
        chore_names = set(Chore.objects.values_list("name", flat=True))
        for person in ["hari", "huanlin", "jaclyn", "tanith"]:
            self.assertEqual(set(CATALOGUE[person]), chore_names)
            for messages in CATALOGUE[person].values():
                self.assertEqual(len(messages), 3)
                self.assertEqual(len(set(messages)), 3)

    def test_repeated_chore_completions_advance_to_a_different_message(self):
        hari = Roommate.objects.create(name="Hari")
        trash = Chore.objects.get(name="Take the trash out")
        first = celebration_for(hari, trash, 1)
        second = celebration_for(hari, trash, 2)
        self.assertNotEqual(first, second)
