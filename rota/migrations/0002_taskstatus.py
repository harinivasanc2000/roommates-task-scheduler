from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("rota", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="TaskStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("task_date", models.DateField()),
                ("completed", models.BooleanField(default=False)),
                ("note", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("chore", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="rota.chore")),
                ("roommate", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="rota.roommate")),
            ],
        ),
        migrations.AddConstraint(model_name="taskstatus", constraint=models.UniqueConstraint(fields=("task_date", "chore", "roommate"), name="one_task_status")),
    ]
