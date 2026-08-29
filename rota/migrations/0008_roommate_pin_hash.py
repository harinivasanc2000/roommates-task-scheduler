from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("rota", "0007_rotaswap")]
    operations = [
        migrations.AddField(model_name="roommate", name="pin_hash", field=models.CharField(blank=True, max_length=128)),
    ]
