from django.db import models
from uuid import uuid4

def generate_patient_id():
    return f"PAT{uuid4().hex[:17].upper()}"


class Patient(models.Model):
    user = models.OneToOneField('authentication.User', on_delete=models.CASCADE)
    patient_id = models.CharField(
        max_length=20,
        unique=True,
        default=generate_patient_id,   # ✅ ensures no empty insert
        editable=False
    )
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=255, blank=True)
    blood_group = models.CharField(max_length=10, blank=True)
    allergies = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.patient_id or self.patient_id.strip() == "":
            self.patient_id = generate_patient_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} - {self.user.first_name} {self.user.last_name}"
