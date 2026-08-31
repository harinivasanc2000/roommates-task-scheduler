from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("rota", "0013_more_features")]

    operations = [
        migrations.AddField(
            model_name="taskstatus",
            name="house_alert",
            field=models.CharField(
                blank=True,
                help_text="An important task update shown prominently to the other roommates.",
                max_length=180,
            ),
        ),
    ]
