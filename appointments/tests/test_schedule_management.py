# appointments/tests/test_schedule_management.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from authentication.models import User
from appointments.models import ClinicianSchedule
from datetime import date, time

@pytest.mark.django_db
class TestAdminScheduleManagement:

    def setup_method(self):
        self.client = APIClient()
        
        # Create user roles
        self.admin = User.objects.create_user(
            username="admin_f011", password="testpass", role="ADMIN"
        )
        self.clinician = User.objects.create_user(
            username="doc_f011", password="testpass", role="CLINICIAN"
        )
        self.patient = User.objects.create_user(
            username="pat_f011", password="testpass", role="PATIENT"
        )
        
        self.manage_url = reverse("admin-schedule-manage")

    def test_admin_can_create_schedule(self):
        """HCRM-F-011: Test that an admin can create a schedule slot."""
        self.client.force_authenticate(user=self.admin)
        
        payload = {
            "clinician": self.clinician.id,
            "date": "2025-12-25",
            "start_time": "09:00:00",
            "end_time": "10:00:00"
        }
        
        response = self.client.post(self.manage_url, payload, format="json")
        
        assert response.status_code == 201
        assert ClinicianSchedule.objects.count() == 1
        assert ClinicianSchedule.objects.first().clinician == self.clinician

    def test_admin_can_delete_schedule(self):
        """HCRM-F-011: Test that an admin can delete a schedule slot."""
        schedule = ClinicianSchedule.objects.create(
            clinician=self.clinician,
            date="2025-12-25",
            start_time="09:00:00",
            end_time="10:00:00"
        )
        delete_url = reverse("admin-schedule-delete", kwargs={"pk": schedule.id})
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(delete_url)
        
        assert response.status_code == 204  # No Content
        assert ClinicianSchedule.objects.count() == 0

    def test_clinician_cannot_create_schedule(self):
        """Test that a non-admin (Clinician) is forbidden."""
        self.client.force_authenticate(user=self.clinician)
        
        payload = { "clinician": self.clinician.id, "date": "2025-12-25" }
        response = self.client.post(self.manage_url, payload, format="json")
        
        assert response.status_code == 403

    def test_patient_cannot_delete_schedule(self):
        """Test that a non-admin (Patient) is forbidden."""
        schedule = ClinicianSchedule.objects.create(
            clinician=self.clinician, date="2025-12-25",
            start_time="09:00:00", end_time="10:00:00"
        )
        delete_url = reverse("admin-schedule-delete", kwargs={"pk": schedule.id})

        self.client.force_authenticate(user=self.patient)
        response = self.client.delete(delete_url)
        
        assert response.status_code == 403
        assert ClinicianSchedule.objects.count() == 1