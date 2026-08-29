from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("rota", "0009_remove_roommate_pin_hash")]
    operations = [
        migrations.CreateModel(
            name="CelebrationCounter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("count", models.PositiveIntegerField(default=0)),
                ("chore", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="rota.chore")),
                ("roommate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="rota.roommate")),
            ],
        ),
        migrations.AddConstraint(model_name="celebrationcounter", constraint=models.UniqueConstraint(fields=("roommate", "chore"), name="one_celebration_counter")),
    ]
