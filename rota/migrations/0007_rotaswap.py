from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("rota", "0006_seed_household")]
    operations = [
        migrations.CreateModel(
            name="RotaSwap",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("requester_week", models.DateField()),
                ("requested_week", models.DateField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("accepted", "Accepted"), ("declined", "Declined")], default="pending", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_swaps", to="rota.roommate")),
                ("requested_with", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="received_swaps", to="rota.roommate")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
