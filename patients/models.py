from django.db import models, transaction

def generate_patient_id():
    from patients.models import Patient
    last_patient = Patient.objects.order_by('-id').first()
    if (
        last_patient
        and last_patient.patient_id
        and last_patient.patient_id.startswith("PAT")
        and last_patient.patient_id[3:].isdigit()
    ):
        new_id = int(last_patient.patient_id[3:]) + 1
    else:
        new_id = 1
    return f"PAT{new_id:06d}"


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
            with transaction.atomic():
                last_patient = Patient.objects.select_for_update().order_by('-id').first()
                if (
                    last_patient
                    and last_patient.patient_id
                    and last_patient.patient_id.startswith("PAT")
                    and last_patient.patient_id[3:].isdigit()
                ):
                    new_id = int(last_patient.patient_id[3:]) + 1
                else:
                    new_id = 1
                self.patient_id = f"PAT{new_id:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} - {self.user.first_name} {self.user.last_name}"
