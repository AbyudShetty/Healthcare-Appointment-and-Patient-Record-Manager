from django.db import models
from authentication.models import User
from patients.models import Patient
from uuid import uuid4

class ClinicianSchedule(models.Model):
    """Manages clinician availability (HCRM-F-004)"""
    
    clinician = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'clinician_schedules'
        unique_together = ['clinician', 'date', 'start_time']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.clinician.get_full_name()} - {self.date} {self.start_time}-{self.end_time}"

class Appointment(models.Model):
    """Appointment booking model (HCRM-F-005)"""

    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
    ]

    appointment_id = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    clinician = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration_minutes = models.IntegerField(default=30)
    reason_for_visit = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointments'
        ordering = ['-appointment_date', '-appointment_time']

    def save(self, *args, **kwargs):
        if not self.appointment_id:
            self.appointment_id = f"APT{uuid4().hex[:17].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.appointment_id} - {self.patient.user.get_full_name()} with {self.clinician.get_full_name()}"
