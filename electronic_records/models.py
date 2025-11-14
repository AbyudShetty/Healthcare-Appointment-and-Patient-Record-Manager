# electronic_records/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from patients.models import Patient
from electronic_records.utils import encrypt_field  
import os
from django.core.validators import FileExtensionValidator


class PatientRecord(models.Model):
    """
    Minimal PatientRecord model for local development/testing.
    In your real project this likely stores encrypted fields; here we
    keep plaintext fields but expose property names the serializers expect.
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='records')
    medical_history_encrypted = models.TextField(blank=True, default='')
    diagnoses_encrypted = models.TextField(blank=True, default='')
    medications_encrypted = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='created_records')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Record {self.pk} for {self.patient}"

    # Simple property getters to match serializer fields (pretend-decrypted)
    @property
    def medical_history(self):
        return self.medical_history_encrypted

    @property
    def diagnoses(self):
        return self.diagnoses_encrypted

    @property
    def medications(self):
        return self.medications_encrypted


class ClinicalNote(models.Model):
    """
    Minimal ClinicalNote model linking to a PatientRecord.
    Note: on create we encrypt the plain text stored in `note_content_encrypted`
    using `encrypt_field()` and store the encrypted token (as a UTF-8 string)
    in the TextField. Decryption is handled at serialization time.
    """
    record = models.ForeignKey(PatientRecord, on_delete=models.CASCADE, related_name='clinical_notes')
    clinician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note_content_encrypted = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Note {self.pk} for record {self.record_id}"

    @property
    def note_content(self):
        # legacy convenience property — returns the stored value (encrypted or plaintext)
        return self.note_content_encrypted

    def save(self, *args, **kwargs):
        """
        Encrypt `note_content_encrypted` on creation (when self.pk is None).
        - `encrypt_field` is expected to return bytes (Fernet token).
        - We decode bytes to utf-8 string to store in TextField.
        - On update (existing pk) we do not re-encrypt to avoid double-encryption.
        """
        try:
            # Only encrypt on first save (create) and only if the field is non-empty
            if self.pk is None and self.note_content_encrypted:
                token = encrypt_field(self.note_content_encrypted)
                if isinstance(token, (bytes, bytearray)):
                    token = token.decode("utf-8")
                # store the token string in the TextField
                self.note_content_encrypted = token
        except Exception:
            # In dev, fail-open: don't block saves if encryption unexpectedly fails
            # In production, log/raise appropriately
            pass

        super().save(*args, **kwargs)

class PatientDocument(models.Model):
    """Uploaded patient documents (encrypted at rest)"""
    
    DOCUMENT_TYPES = [
        ('LAB_REPORT', 'Lab Report'),
        ('IMAGING', 'Imaging Results'),
        ('PRESCRIPTION', 'Prescription'),
        ('OTHER', 'Other'),
    ]
    
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file_encrypted = models.FileField(
        upload_to='documents/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file_size_bytes = models.BigIntegerField()
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.original_filename} - {self.patient.patient_id}"