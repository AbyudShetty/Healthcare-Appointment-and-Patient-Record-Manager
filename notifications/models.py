from django.db import models
from django.utils import timezone


class ReminderJob(models.Model):
    appointment = models.OneToOneField('appointments.Appointment', on_delete=models.CASCADE, related_name='reminder_job')
    due_at = models.DateTimeField(db_index=True)
    state = models.CharField(max_length=16, default='PENDING', db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    claim_token = models.CharField(max_length=32, blank=True)
    last_error = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(default=timezone.now)
