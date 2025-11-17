"""
Quick performance test runner
Verifies NF-003 (load), NF-004 (DB speed), and related search limits.
"""

import pytest
import time
from django.test import TestCase
from django.contrib.auth import get_user_model
from patients.models import Patient
from electronic_records.models import PatientRecord
from rest_framework.test import APIRequestFactory, force_authenticate
from electronic_records.views import PatientRecordSearchView

User = get_user_model()


@pytest.mark.django_db
class TestBasicPerformance(TestCase):
    """Quick smoke test for performance limits"""

    def setUp(self):
        # Create sample clinician and patients
        self.clinician = User.objects.create_user(
            username="clinician_perf",
            role="CLINICIAN",
            password="testpass"
        )
        self.patients = [
            Patient.objects.create(
                user=User.objects.create_user(
                    username=f"patient_{i}",
                    role="PATIENT"
                )
            )
            for i in range(100)
        ]

        for patient in self.patients:
            PatientRecord.objects.create(
                patient=patient,
                medical_history_encrypted="Test history",
                diagnoses_encrypted="Diabetes Mellitus",
                medications_encrypted="Metformin"
            )

    def test_patient_search_within_7s(self):
        """Ensure F-015 search executes within 7 seconds"""
        factory = APIRequestFactory()
        request = factory.get("/api/v1/records/search/?q=patient")
        force_authenticate(request, user=self.clinician)

        view = PatientRecordSearchView.as_view()
        start_time = time.time()
        response = view(request)
        duration = time.time() - start_time

        assert response.status_code == 200
        assert duration <= 7.0, f"Search took {duration:.2f}s — exceeds 7s limit"


    def test_record_retrieval_under_5s(self):
        """Ensure record retrieval under 5 seconds"""
        start_time = time.time()
        rec = PatientRecord.objects.select_related("patient__user").first()
        _ = rec.medical_history
        duration = time.time() - start_time
        assert duration <= 5.0, f"Record retrieval took {duration:.2f}s"
