# appointments/migrations/0003_merge.py
from django.db import migrations

class Migration(migrations.Migration):
    # make these exactly the filenames of the two conflicting migrations shown in CI
    dependencies = [
        ('appointments', '0002_alter_appointment_id'),
        ('appointments', '0002_alter_appointment_id_clinicianschedule'),
    ]

    operations = [
        # no schema operations needed — this file simply resolves the migration graph
    ]
