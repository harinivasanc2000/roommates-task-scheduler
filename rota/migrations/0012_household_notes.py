from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("rota", "0011_helpful_features")]

    operations = [
        migrations.CreateModel(
            name="HouseholdNote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.CharField(max_length=280)),
                ("pinned", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notes", to="rota.roommate")),
            ],
            options={"ordering": ["-pinned", "-created_at"]},
        ),
    ]
