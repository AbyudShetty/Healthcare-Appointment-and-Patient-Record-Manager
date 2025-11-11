import pytest
import time
from datetime import date, time as dtime
from django.urls import reverse
from rest_framework.test import APIClient
from authentication.models import User
from patients.models import Patient
from appointments.models import Appointment
from unittest.mock import patch


@pytest.mark.django_db(transaction=True)
class TestAppointmentBookingView:
    """End-to-end tests for appointment booking (HCRM-F-005, HCRM-NF-001)"""

    def setup_method(self):
        self.client = APIClient()
        self.clinician = User.objects.create_user(
            username="doc_hcrm5",
            password="testpass",
            role="CLINICIAN",
            first_name="Jane",
            last_name="Doe",
        )
        self.patient_user = User.objects.create_user(
            username="pat_hcrm5",
            password="testpass",
            role="PATIENT",
            first_name="John",
            last_name="Smith",
        )
        self.patient = Patient.objects.create(user=self.patient_user)
        self.client.force_authenticate(user=self.patient_user)
        self.url = reverse("appointment-book")

    @patch("notifications.tasks.schedule_appointment_reminder.delay", lambda x: None)
    def test_successful_appointment_booking(self):
        """HCRM-F-005: Patient can book an available slot successfully."""
        payload = {
            "patient": self.patient.id,
            "clinician": self.clinician.id,
            "appointment_date": date.today().strftime("%Y-%m-%d"),
            "appointment_time": dtime(10, 0).strftime("%H:%M:%S"),
            "reason_for_visit": "General check-up",
        }

        start_time = time.time()
        response = self.client.post(self.url, payload, format="json")
        duration = time.time() - start_time

        assert response.status_code == 201, f"Unexpected response: {response.data}"
        data = getattr(response, "data", None) or {}
        assert "appointment_id" in data, "Appointment ID missing in response"
        assert Appointment.objects.filter(clinician=self.clinician).count() == 1
        assert duration <= 10, f"Booking exceeded 10s limit: {duration:.2f}s"

    def test_conflicting_appointment_returns_409(self):
        """HCRM-F-005: Prevent double booking for same clinician, date & time."""
        Appointment.objects.create(
            patient=self.patient,
            clinician=self.clinician,
            appointment_date=date.today(),
            appointment_time=dtime(11, 0),
            status="SCHEDULED",
        )

        payload = {
            "patient": self.patient.id,
            "clinician": self.clinician.id,
            "appointment_date": date.today().strftime("%Y-%m-%d"),
            "appointment_time": dtime(11, 0).strftime("%H:%M:%S"),
            "reason_for_visit": "Conflict test",
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 409
        assert "no longer available" in response.data["error"]

    def test_unauthenticated_user_cannot_book(self):
        """Ensure only authenticated patients can book appointments."""
        self.client.logout()
        payload = {
            "patient": self.patient.id,
            "clinician": self.clinician.id,
            "appointment_date": date.today().strftime("%Y-%m-%d"),
            "appointment_time": dtime(12, 0).strftime("%H:%M:%S"),
            "reason_for_visit": "Unauthorized test",
        }

        response = self.client.post(self.url, payload, format="json")

        assert response.status_code == 401