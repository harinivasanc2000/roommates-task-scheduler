from datetime import date

from django.db import migrations


def seed_household(apps, schema_editor):
    Roommate = apps.get_model("rota", "Roommate")
    RotaSettings = apps.get_model("rota", "RotaSettings")
    profiles = [
        ("Hari", "🐶", "Woof woof, Hari! Ready to make this week pawsome?"),
        ("Huanlin", "🦁", "欢迎回来，Huanlin！今天也一起把家里照顾好吧。"),
        ("Jaclyn", "🦘", "G’day, Jaclyn! Let’s get this place looking bonzer."),
        ("Tanith", "🐱", "Howzit, Tanith! Cooper says you’ve got this."),
    ]
    people = {}
    for name, avatar, greeting in profiles:
        person, _ = Roommate.objects.get_or_create(name=name, defaults={
            "avatar": avatar, "greeting": greeting, "active": True,
        })
        changed = []
        if not person.avatar or person.avatar == "🙂":
            person.avatar = avatar
            changed.append("avatar")
        if not person.greeting:
            person.greeting = greeting
            changed.append("greeting")
        if changed:
            person.save(update_fields=changed)
        people[name] = person

    settings, _ = RotaSettings.objects.get_or_create(pk=1)
    settings.rotation_start = date(2026, 8, 31)
    settings.starting_roommate = people["Huanlin"]
    settings.save(update_fields=["rotation_start", "starting_roommate"])


class Migration(migrations.Migration):
    dependencies = [("rota", "0005_rotasettings_starting_roommate")]
    operations = [migrations.RunPython(seed_household, migrations.RunPython.noop)]
