from datetime import datetime, timedelta

from django.db import migrations
from django.utils import timezone


def backfill_reminders(apps, schema_editor):
    Appointment = apps.get_model('appointments', 'Appointment')
    ReminderJob = apps.get_model('notifications', 'ReminderJob')
    database = schema_editor.connection.alias
    now = timezone.now()
    for appointment in Appointment.objects.using(database).filter(status='SCHEDULED', appointment_date__gte=timezone.localdate()).iterator():
        start = timezone.make_aware(datetime.combine(appointment.appointment_date, appointment.appointment_time))
        if start > now:
            ReminderJob.objects.using(database).get_or_create(
                appointment_id=appointment.pk,
                defaults={'due_at': max(start - timedelta(hours=24), now)},
            )


class Migration(migrations.Migration):
    dependencies = [('notifications', '0001_initial')]
    operations = [migrations.RunPython(backfill_reminders, migrations.RunPython.noop)]
