import pytest
from unittest.mock import patch
from datetime import date, time
from appointments.models import Appointment
from patients.models import Patient
from authentication.models import User
from notifications.tasks import schedule_appointment_reminder


@pytest.mark.django_db
class TestAppointmentReminderTask:
    """Unit tests for schedule_appointment_reminder task (HCRM-F-006)"""

    @patch("notifications.tasks.send_mail")
    def test_sends_email_reminder_successfully(self, mock_send_mail):
        """Should send an email reminder when appointment exists"""
        # Setup: create test data
        user = User.objects.create_user(
            username="john",
            email="john@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            role="PATIENT",
        )
        patient = Patient.objects.create(user=user)
        clinician = User.objects.create_user(
            username="doc",
            email="doc@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Smith",
            role="CLINICIAN",
        )

        appointment = Appointment.objects.create(
            patient=patient,
            clinician=clinician,
            appointment_date=date.today(),
            appointment_time=time(12, 0),
        )

        # Execute
        result = schedule_appointment_reminder(appointment.id)

        # Assert
        mock_send_mail.assert_called_once()
        assert "Reminder sent for appointment" in result

    def test_returns_error_if_appointment_not_found(self):
        """Should return not found message if invalid appointment_id"""
        result = schedule_appointment_reminder(9999)
        assert "not found" in result
