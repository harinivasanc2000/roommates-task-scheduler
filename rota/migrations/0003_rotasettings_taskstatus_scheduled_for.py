import rota.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("rota", "0002_taskstatus")]
    operations = [
        migrations.CreateModel(name="RotaSettings", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("rotation_start", models.DateField(default=rota.models.upcoming_monday)),
        ]),
        migrations.AddField(model_name="taskstatus", name="scheduled_for", field=models.DateField(blank=True, null=True)),
    ]
