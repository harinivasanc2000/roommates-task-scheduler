from datetime import date

from django.db import migrations, models
import django.db.models.deletion


def set_current_rotation(apps, schema_editor):
    RotaSettings = apps.get_model("rota", "RotaSettings")
    Roommate = apps.get_model("rota", "Roommate")
    huanlin = Roommate.objects.filter(name__iexact="Huanlin").first()
    settings, _ = RotaSettings.objects.get_or_create(pk=1)
    settings.rotation_start = date(2026, 8, 31)
    settings.starting_roommate = huanlin
    settings.save(update_fields=["rotation_start", "starting_roommate"])


class Migration(migrations.Migration):
    dependencies = [("rota", "0004_roommate_identity")]
    operations = [
        migrations.AddField(
            model_name="rotasettings",
            name="starting_roommate",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="+", to="rota.roommate"),
        ),
        migrations.RunPython(set_current_rotation, migrations.RunPython.noop),
    ]
