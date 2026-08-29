from django.db import migrations, models


def starter_data(apps, schema_editor):
    Chore = apps.get_model("rota", "Chore")
    for name, frequency, weekday in [
        ("Take the trash out", "alternate_days", 0),
        ("Clean the kitchen", "weekly", 0),
        ("Clean the toilet", "weekly", 1),
        ("Vacuum", "weekly", 3),
        ("Mop the floor", "weekly", 5),
        ("Check essential toiletries & supplies", "weekly", 6),
    ]:
        Chore.objects.create(name=name, frequency=frequency, weekday=weekday)


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name="Chore", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=100, unique=True)),
            ("frequency", models.CharField(choices=[("weekly", "Once a week"), ("alternate_days", "Every other day")], default="weekly", max_length=20)),
            ("weekday", models.PositiveSmallIntegerField(choices=[(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")], default=5, help_text="Day used for once-a-week chores.")),
            ("active", models.BooleanField(default=True)),
        ], options={"ordering": ["name"]}),
        migrations.CreateModel(name="Roommate", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=80, unique=True)),
            ("email", models.EmailField(blank=True, max_length=254)),
            ("active", models.BooleanField(default=True)),
        ], options={"ordering": ["name"]}),
        migrations.RunPython(starter_data, migrations.RunPython.noop),
    ]
