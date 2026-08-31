from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .celebrations import CATALOGUE, celebration_for
from .models import CelebrationCounter, Chore, Roommate, RotaSettings, RotaSwap, TaskStatus
from .services import build_week, monday_for, week_owner
from .views import _off_week_message


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
        self.assertContains(response, 'aria-label="Change appearance"')
        self.assertContains(response, '<body data-theme="midnight">')
        self.assertContains(response, "Continue without choosing")
        alex = Roommate.objects.get(name="Alex")
        self.choose(alex)
        calendar = self.client.get(reverse("rota:calendar"), {"week": "2026-08-24", "person": Roommate.objects.get(name="Zara").id})
        self.assertEqual(calendar["Content-Type"], "text/calendar; charset=utf-8")
        self.assertIn(b"BEGIN:VCALENDAR", calendar.content)
        self.assertIn(b"\r\n", calendar.content)
        self.assertNotIn(b"\n", calendar.content.replace(b"\r\n", b""))
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

    def test_next_task_card_advances_after_completion(self):
        alex = Roommate.objects.get(name="Alex")
        current_week = monday_for(timezone.localdate())
        settings = RotaSettings.load()
        settings.rotation_start = current_week
        settings.starting_roommate = alex
        settings.save()
        self.choose(alex)
        response = self.client.get(reverse("rota:schedule"), {"week": current_week.isoformat()})
        first_task = response.context["next_task"]
        self.assertEqual(first_task.roommate, alex)
        self.assertFalse(first_task.completed)
        self.assertContains(response, "UP NEXT FOR YOU")

        self.client.post(reverse("rota:update_task"), {
            "task_date": first_task.original_date.isoformat(),
            "chore_id": first_task.chore.id,
            "roommate_id": alex.id,
            "completed": "true",
        })
        response = self.client.get(reverse("rota:schedule"), {"week": current_week.isoformat()})
        self.assertNotEqual(
            (response.context["next_task"].original_date, response.context["next_task"].chore.id),
            (first_task.original_date, first_task.chore.id),
        )

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

    def test_default_view_starts_with_the_real_current_week(self):
        response = self.client.get(reverse("rota:schedule"))
        self.assertEqual(response.context["week_start"], monday_for(timezone.localdate()))

    def test_off_week_greeting_names_owner_and_next_turn(self):
        alex = Roommate.objects.get(name="Alex")
        zara = Roommate.objects.get(name="Zara")
        current_week = monday_for(timezone.localdate())
        settings = RotaSettings.load()
        settings.rotation_start = current_week
        settings.starting_roommate = alex
        settings.save()
        self.choose(zara)

        response = self.client.get(reverse("rota:schedule"))

        self.assertEqual(response.context["current_owner"], alex)
        self.assertEqual(response.context["next_personal_week_start"], current_week + timedelta(days=7))
        self.assertContains(response, "Chill, Zara — Alex has this week covered")
        self.assertContains(response, "YOUR NEXT ROTA")
        self.assertNotContains(response, "UP NEXT FOR YOU")

    def test_personalized_off_week_messages_match_housemate_characters(self):
        owner = Roommate.objects.get(name="Alex")
        examples = {
            "Hari": "Paws up",
            "Huanlin": "这周轻松一下",
            "Jaclyn": "No worries",
            "Tanith": "Cooper says relax",
        }
        for name, phrase in examples.items():
            person = Roommate(name=name)
            self.assertIn(phrase, _off_week_message(person, owner))

    def test_other_roommates_completion_and_full_note_are_read_only(self):
        alex = Roommate.objects.get(name="Alex")
        zara = Roommate.objects.get(name="Zara")
        current_week = monday_for(timezone.localdate())
        settings = RotaSettings.load()
        settings.rotation_start = current_week
        settings.starting_roommate = alex
        settings.save()
        item = build_week(current_week)[0]
        TaskStatus.objects.create(
            task_date=item.date,
            chore=item.chore,
            roommate=alex,
            completed=True,
            note="Please leave the clean cloth beside the sink for everyone.",
        )
        self.choose(zara)

        response = self.client.get(reverse("rota:schedule"))
        html = response.content.decode()
        task_html = html.split('aria-label="Read-only task for Alex"', 1)[1].split("</article>", 1)[0]

        self.assertIn("Completed", task_html)
        self.assertIn("Please leave the clean cloth beside the sink for everyone.", task_html)
        self.assertNotIn("<form", task_html)
        self.assertNotIn("openTask", task_html)

    def test_task_owner_can_alert_housemates_and_alert_survives_completion(self):
        alex = Roommate.objects.get(name="Alex")
        zara = Roommate.objects.get(name="Zara")
        current_week = monday_for(timezone.localdate())
        settings = RotaSettings.load()
        settings.rotation_start = current_week
        settings.starting_roommate = alex
        settings.save()
        item = build_week(current_week)[0]
        alert = "Floor is wet until 8pm — please use the other hallway."
        self.choose(alex)
        self.client.post(reverse("rota:update_task"), {
            "task_date": item.date.isoformat(),
            "chore_id": item.chore.id,
            "roommate_id": alex.id,
            "house_alert": alert,
        })

        self.choose(zara)
        response = self.client.get(reverse("rota:schedule"), {"week": (current_week + timedelta(days=35)).isoformat()})
        self.assertContains(response, "HOUSE HEADS-UP")
        self.assertContains(response, alert)

        forbidden = self.client.post(reverse("rota:update_task"), {
            "task_date": item.date.isoformat(),
            "chore_id": item.chore.id,
            "roommate_id": alex.id,
            "house_alert": "Changed by someone else",
        })
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(TaskStatus.objects.get().house_alert, alert)

        self.choose(alex)
        self.client.post(reverse("rota:update_task"), {
            "task_date": item.date.isoformat(),
            "chore_id": item.chore.id,
            "roommate_id": alex.id,
            "completed": "true",
        })
        self.choose(zara)
        response = self.client.get(reverse("rota:schedule"))
        self.assertContains(response, alert)
        self.assertContains(response, "task completed")

        self.choose(alex)
        self.client.post(reverse("rota:update_task"), {
            "task_date": item.date.isoformat(),
            "chore_id": item.chore.id,
            "roommate_id": alex.id,
            "house_alert": "",
        })
        self.choose(zara)
        response = self.client.get(reverse("rota:schedule"))
        self.assertNotContains(response, alert)
        self.assertNotContains(response, "HOUSE HEADS-UP")

    def test_bulk_complete_today_only_changes_selected_roommates_tasks(self):
        today = date.today()
        owner = week_owner(today)
        self.choose(owner)
        today_items = [item for item in build_week(today) if item.date == today]

        response = self.client.post(reverse("rota:bulk_complete_today"))

        self.assertEqual(response.status_code, 302)
        for item in today_items:
            self.assertTrue(TaskStatus.objects.get(
                task_date=item.date, chore=item.chore, roommate=owner
            ).completed)
        self.assertFalse(TaskStatus.objects.exclude(roommate=owner).exists())

    def test_bulk_complete_today_requires_an_identity(self):
        response = self.client.post(reverse("rota:bulk_complete_today"))
        self.assertEqual(response.status_code, 403)

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
        self.assertContains(response, "See Zara’s current tasks and notes")
        self.assertContains(response, "Read only")

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
