from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("rota", "0008_roommate_pin_hash")]
    operations = [migrations.RemoveField(model_name="roommate", name="pin_hash")]
