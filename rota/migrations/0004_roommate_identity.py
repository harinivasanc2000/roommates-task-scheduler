from django.db import migrations, models


def personalise_roommates(apps, schema_editor):
    Roommate = apps.get_model("rota", "Roommate")
    profiles = {
        "hari": ("🐶", "Woof woof, Hari! Ready to make this week pawsome?"),
        "huanlin": ("🦁", "欢迎回来，Huanlin！今天也一起把家里照顾好吧。"),
        "hualin": ("🦁", "欢迎回来，Hualin！今天也一起把家里照顾好吧。"),
        "jaclyn": ("🦘", "G’day, Jaclyn! Let’s get this place looking bonzer."),
        "tanith": ("🐱", "Howzit, Tanith! Cooper says you’ve got this."),
    }
    for roommate in Roommate.objects.all():
        avatar, greeting = profiles.get(roommate.name.lower(), ("🙂", f"Welcome back, {roommate.name}!"))
        roommate.avatar, roommate.greeting = avatar, greeting
        roommate.save(update_fields=["avatar", "greeting"])


class Migration(migrations.Migration):
    dependencies = [("rota", "0003_rotasettings_taskstatus_scheduled_for")]
    operations = [
        migrations.AddField(model_name="roommate", name="avatar", field=models.CharField(default="🙂", max_length=8)),
        migrations.AddField(model_name="roommate", name="greeting", field=models.CharField(blank=True, max_length=240)),
        migrations.RunPython(personalise_roommates, migrations.RunPython.noop),
    ]
