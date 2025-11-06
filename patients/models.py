from django.db import models
from authentication.models import User

class Patient(models.Model):
    """Patient profile model (HCRM-F-001)"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    patient_id = models.CharField(max_length=20, unique=True, editable=False)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    blood_group = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
    
    def save(self, *args, **kwargs):
        if not self.patient_id:
            # Generate unique patient ID
            last_patient = Patient.objects.order_by('-id').first()
            if last_patient:
                new_id = int(last_patient.patient_id[3:]) + 1
            else:
                new_id = 1
            self.patient_id = f"PAT{new_id:06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.patient_id} - {self.user.get_full_name()}"