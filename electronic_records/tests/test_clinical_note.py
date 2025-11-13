# electronic_records/tests/test_clinical_note.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from authentication.models import User
from patients.models import Patient
from electronic_records.models import PatientRecord, ClinicalNote
from electronic_records.utils import decrypt_field #

@pytest.mark.django_db
class TestClinicalNoteCreate:

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("clinical-note-add")

        # Create users
        self.clinician = User.objects.create_user(
            username="doc_f009", password="testpass", role="CLINICIAN"
        )
        self.patient_user = User.objects.create_user(
            username="pat_f009", password="testpass", role="PATIENT"
        )

        # Create patient profile and a record
        self.patient = Patient.objects.create(user=self.patient_user)
        self.record = PatientRecord.objects.create(
            patient=self.patient, 
            created_by=self.clinician
        )

    def test_clinician_can_add_note(self):
        """
        HCRM-F-009: Test that an authenticated clinician can add a note.
        """
        self.client.force_authenticate(user=self.clinician)

        payload = {
            "record_id": self.record.id,
            "note_content": "Patient reports mild headache."
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 201
        assert ClinicalNote.objects.count() == 1

        # Verify the note content was encrypted and saved correctly
        new_note = ClinicalNote.objects.first()
        assert new_note.record == self.record
        assert decrypt_field(new_note.note_content_encrypted) == "Patient reports mild headache."

    def test_patient_cannot_add_note(self):
        """
        Test that a user with the 'PATIENT' role is forbidden.
        """
        self.client.force_authenticate(user=self.patient_user)

        payload = {
            "record_id": self.record.id,
            "note_content": "I think I have a cold."
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 403
        assert ClinicalNote.objects.count() == 0

    def test_add_note_to_nonexistent_record_fails(self):
        """
        Test that adding a note to a record_id that doesn't exist
        returns a 404 error.
        """
        self.client.force_authenticate(user=self.clinician)

        payload = {
            "record_id": 99999, # Non-existent ID
            "note_content": "This note goes nowhere."
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 404