from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("rota", "0010_taskstatus_completion_count")]

    operations = [
        migrations.AddField(
            model_name="roommate",
            name="away_until",
            field=models.DateField(
                blank=True,
                null=True,
                help_text="While set and in the future, this roommate is skipped in the weekly rotation.",
            ),
        ),
        migrations.AddField(
            model_name="taskstatus",
            name="skipped",
            field=models.BooleanField(default=False),
        ),
    ]
