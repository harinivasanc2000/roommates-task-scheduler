from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("rota", "0012_household_notes")]

    operations = [
        migrations.AddField(
            model_name="householdnote",
            name="reactions",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="chore",
            name="effort",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Light"), (2, "Medium"), (3, "Heavy")],
                default=1,
                help_text="Used for fairness weighting.",
            ),
        ),
    ]
