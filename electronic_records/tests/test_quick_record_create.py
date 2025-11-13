# electronic_records/tests/test_quick_record_create.py
import os
from datetime import date
from cryptography.fernet import Fernet

# Ensure encryption env var used by the project's encryption utilities is set BEFORE Django imports modules that use it.
# The encryption utility in your repo used ENV_KEY = "HCRM_ENCRYPTION_KEY"
os.environ.setdefault("HCRM_ENCRYPTION_KEY", Fernet.generate_key().decode())

import pytest
from rest_framework.test import APIClient
from django.urls import reverse

from authentication.models import User
from patients.models import Patient
from electronic_records.models import PatientRecord

pytestmark = pytest.mark.django_db(transaction=True)


class TestQuickRecordCreateView:
    """
    Tests for QuickRecordCreateView (POST /api/v1/records/quick-create/)
    """

    def setup_method(self):
        self.client = APIClient()

        # Clinician user
        self.clinician = User.objects.create_user(
            username="clinician_qr",
            password="testpass",
            role="CLINICIAN",
            first_name="Clin",
            last_name="Ician"
        )

        # Admin user (also allowed)
        self.admin = User.objects.create_user(
            username="admin_qr",
            password="testpass",
            role="ADMIN",
            first_name="Ad",
            last_name="Min"
        )

        # Patient user + Patient record (ensure patient_id exists)
        self.patient_user = User.objects.create_user(
            username="patient_qr",
            password="testpass",
            role="PATIENT",
            first_name="Pat",
            last_name="One"
        )

        # Create patient with explicit patient_id field that your view expects
        # If your Patient model requires different fields, adapt accordingly
        self.patient = Patient.objects.create(user=self.patient_user, patient_id="PAT000999")

        # Non-clinician user
        self.patient_other = User.objects.create_user(
            username="patient_other",
            password="testpass",
            role="PATIENT",
            first_name="Other",
            last_name="Patient"
        )

        # URL - adjust if your project mounts API under a prefix
        # The sprint instructions said: /api/v1/records/quick-create/
        self.url = "/api/v1/records/quick-create/"

    def test_clinician_can_create_quick_record(self):
        """Clinician should create a minimal PatientRecord (201)"""
        payload = {
            "patient_id": self.patient.patient_id,
            "medical_history": "Patient feels fine",
            "diagnoses": "Routine checkup",
            "medications": "None"
        }

        self.client.force_authenticate(user=self.clinician)
        resp = self.client.post(self.url, payload, format="json")

        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}. Response: {resp.data}"

        # Assert a PatientRecord was created for this patient
        recs = PatientRecord.objects.filter(patient=self.patient)
        assert recs.exists(), "Expected a PatientRecord to have been created"

        record = recs.latest("created_at") if hasattr(recs, "latest") else recs.first()

        # Check created_by and that encrypted fields are not plain text (basic sanity)
        assert record.created_by == self.clinician or record.created_by.username == self.clinician.username
        assert record.medical_history_encrypted != payload["medical_history"]
        assert record.diagnoses_encrypted != payload["diagnoses"]
        assert record.medications_encrypted != payload["medications"]

    def test_admin_can_create_quick_record(self):
        """Admin role should also be able to quick-create a record"""
        payload = {
            "patient_id": self.patient.patient_id,
            "medical_history": "Admin entry",
            "diagnoses": "Admin diag",
            "medications": "Admin meds"
        }
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(self.url, payload, format="json")
        assert resp.status_code == 201
        assert PatientRecord.objects.filter(patient=self.patient).count() >= 1

    def test_non_clinician_forbidden(self):
        """A regular patient (role=PATIENT) should get 403 Forbidden"""
        payload = {
            "patient_id": self.patient.patient_id,
            "medical_history": "Not allowed",
        }
        self.client.force_authenticate(user=self.patient_other)
        resp = self.client.post(self.url, payload, format="json")
        assert resp.status_code == 403

    def test_missing_patient_returns_404(self):
        """If patient_id does not exist, view should return 404 Not Found"""
        payload = {
            "patient_id": "NON_EXISTENT_ID",
            "medical_history": "Missing patient",
        }
        self.client.force_authenticate(user=self.clinician)
        resp = self.client.post(self.url, payload, format="json")
        assert resp.status_code == 404
