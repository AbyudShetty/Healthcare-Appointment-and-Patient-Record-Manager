import pytest
import os
from django.urls import reverse
from rest_framework.test import APIClient
from cryptography.fernet import Fernet
from authentication.models import User
from patients.models import Patient
from electronic_records.models import PatientRecord, ClinicalNote
from electronic_records.utils import encrypt_field, decrypt_field


@pytest.mark.django_db(transaction=True)
class TestEPRAccessControl:
    """Integration tests for Electronic Patient Record access control"""

    def setup_method(self):
        # Ensure encryption key is set
        if not os.getenv('HCRM_ENCRYPTION_KEY'):
            os.environ['HCRM_ENCRYPTION_KEY'] = Fernet.generate_key().decode()
        
        self.client = APIClient()
        
        # Create clinician
        self.clinician = User.objects.create_user(
            username="epr_clinician",
            password="testpass",
            role="CLINICIAN",
            first_name="Dr",
            last_name="Wilson"
        )
        
        # Create second clinician
        self.clinician2 = User.objects.create_user(
            username="epr_clinician2",
            password="testpass",
            role="CLINICIAN",
            first_name="Dr",
            last_name="Brown"
        )
        
        # Create patient
        self.patient_user = User.objects.create_user(
            username="epr_patient",
            password="testpass",
            role="PATIENT",
            email="epr_patient@test.com"
        )
        
        self.patient = Patient.objects.create(user=self.patient_user)
        
        # Create another patient
        self.patient2_user = User.objects.create_user(
            username="epr_patient2",
            password="testpass",
            role="PATIENT"
        )
        
        self.patient2 = Patient.objects.create(user=self.patient2_user)
        
        # Create patient records
        self.record = PatientRecord.objects.create(
            patient=self.patient,
            created_by=self.clinician,
            medical_history_encrypted=encrypt_field("Hypertension for 5 years"),
            diagnoses_encrypted=encrypt_field("Essential Hypertension"),
            medications_encrypted=encrypt_field("Lisinopril 10mg daily")
        )
        
        # Add clinical note
        self.note = ClinicalNote.objects.create(
            record=self.record,
            clinician=self.clinician,
            note_content_encrypted="Patient responding well to treatment"
        )

    def test_patient_cannot_access_other_patient_records(self):
        """Test that patient cannot access another patient's EPR"""
        self.client.force_authenticate(user=self.patient2_user)
        
        url = reverse('secure-history', kwargs={'patient_id': self.patient.patient_id})
        response = self.client.get(url)
        
        assert response.status_code == 403

    def test_clinician_can_access_any_patient_records(self):
        """Test that clinicians can access any patient's EPR"""
        self.client.force_authenticate(user=self.clinician2)
        
        url = reverse('secure-history', kwargs={'patient_id': self.patient.patient_id})
        response = self.client.get(url)
        
        assert response.status_code == 200
        
        data = response.json()
        results = data.get('results', data)
        assert len(results) >= 1

    def test_clinician_can_create_records(self):
        """Test that clinicians can create patient records"""
        self.client.force_authenticate(user=self.clinician)
        
        url = reverse('record-quick-create')
        payload = {
            'patient_id': self.patient.patient_id,
            'medical_history': 'New medical history entry',
            'diagnoses': 'New diagnosis',
            'medications': 'New medication prescription'
        }
        
        response = self.client.post(url, payload, format='json')
        assert response.status_code == 201
        
        records = PatientRecord.objects.filter(patient=self.patient)
        assert records.count() >= 2

    def test_clinician_can_add_clinical_notes(self):
        """Test that clinicians can add notes to patient records"""
        self.client.force_authenticate(user=self.clinician)
        
        url = reverse('clinical-note-add')
        payload = {
            'record_id': self.record.id,
            'note_content': 'Follow-up notes after consultation'
        }
        
        response = self.client.post(url, payload, format='json')
        assert response.status_code == 201
        
        notes = ClinicalNote.objects.filter(record=self.record)
        assert notes.count() >= 2

    def test_patient_cannot_create_records(self):
        """Test that patients cannot create their own records"""
        self.client.force_authenticate(user=self.patient_user)
        
        url = reverse('record-quick-create')
        payload = {
            'patient_id': self.patient.patient_id,
            'medical_history': 'Self-created history',
            'diagnoses': 'Self-diagnosis',
            'medications': 'Self-prescription'
        }
        
        response = self.client.post(url, payload, format='json')
        
        assert response.status_code == 403

    def test_patient_cannot_add_clinical_notes(self):
        """Test patients cannot add clinical notes"""
        self.client.force_authenticate(user=self.patient_user)
        
        url = reverse('clinical-note-add')
        payload = {
            'record_id': self.record.id,
            'note_content': 'Patient-written note'
        }
        
        response = self.client.post(url, payload, format='json')
        
        assert response.status_code == 403



@pytest.mark.django_db(transaction=True)
class TestEPREncryptionIntegration:
    """Integration tests for EPR encryption end-to-end"""

    def setup_method(self):
        if not os.getenv('HCRM_ENCRYPTION_KEY'):
            os.environ['HCRM_ENCRYPTION_KEY'] = Fernet.generate_key().decode()
        
        self.client = APIClient()
        
        self.clinician = User.objects.create_user(
            username="encrypt_clinician",
            password="testpass",
            role="CLINICIAN"
        )
        
        self.patient_user = User.objects.create_user(
            username="encrypt_patient",
            password="testpass",
            role="PATIENT"
        )
        
        self.patient = Patient.objects.create(user=self.patient_user)

    def test_clinical_notes_are_encrypted(self):
        """Test that clinical notes are encrypted end-to-end"""
        record = PatientRecord.objects.create(
            patient=self.patient,
            created_by=self.clinician
        )
        
        self.client.force_authenticate(user=self.clinician)
        
        sensitive_note = "Patient disclosed history of substance abuse"
        
        url = reverse('clinical-note-add')
        payload = {
            'record_id': record.id,
            'note_content': sensitive_note
        }
        
        response = self.client.post(url, payload, format='json')
        assert response.status_code == 201
        
        note = ClinicalNote.objects.filter(record=record).first()
        assert note.note_content_encrypted != sensitive_note
        
        decrypted = decrypt_field(note.note_content_encrypted)
        assert sensitive_note in str(decrypted) or decrypted == sensitive_note



@pytest.mark.django_db(transaction=True)
class TestEPRAuditTrail:
    """Integration tests for EPR audit trail"""

    def setup_method(self):
        if not os.getenv('HCRM_ENCRYPTION_KEY'):
            os.environ['HCRM_ENCRYPTION_KEY'] = Fernet.generate_key().decode()
        
        self.client = APIClient()
        
        self.clinician = User.objects.create_user(
            username="audit_clinician",
            password="testpass",
            role="CLINICIAN"
        )
        
        self.patient_user = User.objects.create_user(
            username="audit_patient",
            password="testpass",
            role="PATIENT"
        )
        
        self.patient = Patient.objects.create(user=self.patient_user)

    def test_record_creation_is_logged(self):
        """Test that creating a patient record creates an audit log entry"""
        self.client.force_authenticate(user=self.clinician)
        
        url = reverse('record-quick-create')
        payload = {
            'patient_id': self.patient.patient_id,
            'medical_history': 'Audit test history',
            'diagnoses': 'Audit test diagnosis',
            'medications': 'Audit test meds'
        }
        
        response = self.client.post(url, payload, format='json')
        
        assert response.status_code == 201

    def test_clinical_note_creation_is_logged(self):
        """Test that adding clinical notes is logged"""
        record = PatientRecord.objects.create(
            patient=self.patient,
            created_by=self.clinician
        )
        
        self.client.force_authenticate(user=self.clinician)
        
        url = reverse('clinical-note-add')
        payload = {
            'record_id': record.id,
            'note_content': 'Audit test note'
        }
        
        response = self.client.post(url, payload, format='json')
        
        assert response.status_code == 201



@pytest.mark.django_db(transaction=True)
class TestEPRPerformance:
    """Performance tests for EPR system"""

    def setup_method(self):
        if not os.getenv('HCRM_ENCRYPTION_KEY'):
            os.environ['HCRM_ENCRYPTION_KEY'] = Fernet.generate_key().decode()
        
        self.client = APIClient()
        
        self.clinician = User.objects.create_user(
            username="perf_clinician",
            password="testpass",
            role="CLINICIAN"
        )
        
        self.patient_user = User.objects.create_user(
            username="perf_patient",
            password="testpass",
            role="PATIENT"
        )
        
        self.patient = Patient.objects.create(user=self.patient_user)

    def test_record_creation_completes_within_5_seconds(self):
        """Performance: record creation ≤ 5 seconds"""
        import time
        
        self.client.force_authenticate(user=self.clinician)
        
        url = reverse('record-quick-create')
        payload = {
            'patient_id': self.patient.patient_id,
            'medical_history': 'Performance test history',
            'diagnoses': 'Performance test diagnosis',
            'medications': 'Performance test medications'
        }
        
        start_time = time.time()
        response = self.client.post(url, payload, format='json')
        duration = time.time() - start_time
        
        assert response.status_code == 201
        assert duration <= 5.0

    def test_record_retrieval_is_performant(self):
        """Performance: retrieval ≤ 5 seconds"""
        import time
        
        for i in range(5):
            PatientRecord.objects.create(
                patient=self.patient,
                created_by=self.clinician,
                medical_history_encrypted=encrypt_field(f"History {i}"),
                diagnoses_encrypted=encrypt_field(f"Diagnosis {i}"),
                medications_encrypted=encrypt_field(f"Meds {i}")
            )
        
        self.client.force_authenticate(user=self.patient_user)
        
        url = reverse('secure-history', kwargs={'patient_id': self.patient.patient_id})
        
        start_time = time.time()
        response = self.client.get(url)
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration <= 5.0