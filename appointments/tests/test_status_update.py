# appointments/tests/test_status_update.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from authentication.models import User
from patients.models import Patient
from appointments.models import Appointment
from datetime import date, time

@pytest.mark.django_db
class TestAppointmentStatusUpdate:

    def setup_method(self):
        self.client = APIClient()
        
        # Create users
        self.admin = User.objects.create_user(
            username="admin_f013", password="testpass", role="ADMIN"
        )
        self.clinician = User.objects.create_user(
            username="doc_f013", password="testpass", role="CLINICIAN"
        )
        self.patient_user = User.objects.create_user(
            username="pat_f013", password="testpass", role="PATIENT"
        )
        self.patient = Patient.objects.create(user=self.patient_user)
        
        # Create a base appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            clinician=self.clinician,
            appointment_date=date(2025, 12, 1),
            appointment_time=time(10, 0),
            status="SCHEDULED"
        )
        
        # Build the URL using the appointment's string ID
        self.url = reverse(
            "appointment-status-update", 
            kwargs={"appointment_id": self.appointment.appointment_id}
        )

    def test_admin_can_mark_no_show(self):
        """HCRM-F-013: Test that an admin can update status to NO_SHOW."""
        self.client.force_authenticate(user=self.admin)
        
        payload = {"status": "NO_SHOW"}
        response = self.client.patch(self.url, payload, format="json")
        
        assert response.status_code == 200
        self.appointment.refresh_from_db()
        assert self.appointment.status == "NO_SHOW"
        assert response.data['status'] == "NO_SHOW"

    def test_clinician_can_mark_completed(self):
        """Test that a clinician can update status to COMPLETED."""
        self.client.force_authenticate(user=self.clinician)
        
        payload = {"status": "COMPLETED"}
        response = self.client.patch(self.url, payload, format="json")
        
        assert response.status_code == 200
        self.appointment.refresh_from_db()
        assert self.appointment.status == "COMPLETED"

    def test_patient_cannot_update_status(self):
        """Test that a Patient is forbidden from updating status."""
        self.client.force_authenticate(user=self.patient_user)
        
        payload = {"status": "COMPLETED"}
        response = self.client.patch(self.url, payload, format="json")
        
        assert response.status_code == 403
        self.appointment.refresh_from_db()
        assert self.appointment.status == "SCHEDULED" # Status did not change

    def test_invalid_status_string_fails(self):
        """Test that sending an invalid status string returns a 400."""
        self.client.force_authenticate(user=self.admin)
        
        payload = {"status": "PENDING"} # Not an allowed choice
        response = self.client.patch(self.url, payload, format="json")
        
        assert response.status_code == 400
        assert "Invalid status" in response.data['error']