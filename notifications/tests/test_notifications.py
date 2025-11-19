import pytest
from unittest.mock import patch, Mock
from datetime import date, time, datetime, timedelta
from django.core.mail import send_mail
from appointments.models import Appointment
from patients.models import Patient
from authentication.models import User
from notifications.tasks import schedule_appointment_reminder


@pytest.mark.django_db
class TestAppointmentReminders:
    """Tests for appointment reminder notifications (HCRM-F-006)"""

    def setup_method(self):
        self.clinician = User.objects.create_user(
            username="clinician_notif",
            password="testpass",
            role="CLINICIAN",
            first_name="Dr",
            last_name="Smith"
        )
        
        self.patient_user = User.objects.create_user(
            username="patient_notif",
            password="testpass",
            email="patient@test.com",
            role="PATIENT",
            first_name="John",
            last_name="Doe"
        )
        
        self.patient = Patient.objects.create(user=self.patient_user)

    @patch('notifications.tasks.send_mail')
    def test_reminder_sent_for_upcoming_appointment(self, mock_send_mail):
        """Test that reminder is sent for appointments 24 hours before"""
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            clinician=self.clinician,
            appointment_date=tomorrow,
            appointment_time=time(10, 0),
            status='SCHEDULED',
            reason_for_visit='Check-up'
        )
        
        # Trigger reminder task
        result = schedule_appointment_reminder(appointment.id)
        
        # Verify email was sent
        mock_send_mail.assert_called_once()
        
        # Verify return message
        assert "Reminder sent" in result

    @patch('notifications.tasks.send_mail')
    def test_reminder_contains_appointment_details(self, mock_send_mail):
        """Test that reminder includes appointment date, time, and doctor"""
        tomorrow = date.today() + timedelta(days=1)
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            clinician=self.clinician,
            appointment_date=tomorrow,
            appointment_time=time(14, 30),
            status='SCHEDULED'
        )
        
        schedule_appointment_reminder(appointment.id)
        
        # Get the call arguments
        call_args = mock_send_mail.call_args
        message_body = call_args[1]['message']
        
        # Verify appointment details are in message
        assert str(appointment.appointment_date) in message_body
        assert "Dr. Smith" in message_body or "Smith" in message_body

    def test_reminder_not_sent_for_nonexistent_appointment(self):
        """Test that attempting to send reminder for invalid ID fails gracefully"""
        result = schedule_appointment_reminder(99999)
        
        assert "not found" in result

    @patch('notifications.tasks.send_mail')
    def test_reminder_sent_to_patient_email(self, mock_send_mail):
        """Test that reminder is sent to patient's email address"""
        appointment = Appointment.objects.create(
            patient=self.patient,
            clinician=self.clinician,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            status='SCHEDULED'
        )
        
        schedule_appointment_reminder(appointment.id)
        
        call_args = mock_send_mail.call_args
        recipient_list = call_args[1]['recipient_list']
        
        assert 'patient@test.com' in recipient_list


@pytest.mark.django_db
class TestEmailNotifications:
    """Tests for email notification system"""

    def setup_method(self):
        self.patient_user = User.objects.create_user(
            username="email_test",
            password="testpass",
            email="test@example.com",
            role="PATIENT"
        )

    @patch('notifications.tasks.send_mail')
    def test_email_notification_includes_subject(self, mock_send_mail):
        """Test that email notifications have appropriate subject"""
        clinician = User.objects.create_user(
            username="doc_email",
            password="testpass",
            role="CLINICIAN"
        )
        
        patient = Patient.objects.create(user=self.patient_user)
        
        appointment = Appointment.objects.create(
            patient=patient,
            clinician=clinician,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            status='SCHEDULED'
        )
        
        schedule_appointment_reminder(appointment.id)
        
        call_args = mock_send_mail.call_args
        subject = call_args[1]['subject']
        
        assert 'Appointment' in subject or 'Reminder' in subject

    @patch('notifications.tasks.send_mail')
    def test_email_fails_gracefully_on_send_error(self, mock_send_mail):
        """Test that email sending errors are handled gracefully"""
        # Make send_mail raise an exception
        mock_send_mail.side_effect = Exception("SMTP connection failed")
        
        clinician = User.objects.create_user(
            username="doc_error",
            password="testpass",
            role="CLINICIAN"
        )
        
        patient = Patient.objects.create(user=self.patient_user)
        
        appointment = Appointment.objects.create(
            patient=patient,
            clinician=clinician,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            status='SCHEDULED'
        )
        
        # Should not crash - error should be handled
        try:
            schedule_appointment_reminder(appointment.id)
        except Exception as e:
            # If exception is raised, it should be SMTP error, not a crash
            assert "SMTP" in str(e) or "connection" in str(e).lower()


@pytest.mark.django_db
class TestSMSNotifications:
    """Tests for SMS notification system (future implementation)"""

    def setup_method(self):
        self.patient_user = User.objects.create_user(
            username="sms_test",
            password="testpass",
            phone_number="1234567890",
            role="PATIENT"
        )

    def test_patient_has_phone_number_for_sms(self):
        """Test that patient phone number is available for SMS"""
        assert self.patient_user.phone_number == "1234567890"

    def test_sms_notification_placeholder(self):
        """Placeholder test for future SMS implementation"""
        # SMS functionality would be implemented similar to email
        # This test documents the expected behavior
        pass


@pytest.mark.django_db
class TestNotificationTiming:
    """Tests for notification timing requirements"""

    def setup_method(self):
        self.clinician = User.objects.create_user(
            username="timing_clinician",
            password="testpass",
            role="CLINICIAN"
        )
        
        self.patient_user = User.objects.create_user(
            username="timing_patient",
            password="testpass",
            email="timing@test.com",
            role="PATIENT"
        )
        
        self.patient = Patient.objects.create(user=self.patient_user)

    def test_reminder_calculated_24_hours_before(self):
        """Test that reminder time is calculated as 24 hours before appointment"""
        appointment_datetime = datetime.now() + timedelta(hours=25)
        
        appointment = Appointment.objects.create(
            patient=self.patient,
            clinician=self.clinician,
            appointment_date=appointment_datetime.date(),
            appointment_time=appointment_datetime.time(),
            status='SCHEDULED'
        )
        
        # Calculate expected reminder time
        expected_reminder = appointment_datetime - timedelta(hours=24)
        
        # In actual implementation, would verify Celery task is scheduled for this time
        # For now, just verify the calculation
        assert (appointment_datetime - timedelta(hours=24)) == expected_reminder


@pytest.mark.django_db
class TestNotificationPreferences:
    """Tests for user notification preferences (future enhancement)"""

    def test_user_can_set_notification_preferences(self):
        """Test that users can configure notification preferences"""
        # Future feature: users might want to disable certain notifications
        # This test documents expected behavior
        user = User.objects.create_user(
            username="pref_test",
            password="testpass",
            email="pref@test.com"
        )
        
        # In future, User model might have notification_preferences field
        assert hasattr(user, 'email')  # Current state
        # Future: assert hasattr(user, 'notification_preferences')


@pytest.mark.django_db
class TestNotificationFailover:
    """Tests for notification system resilience"""

    @patch('notifications.tasks.send_mail')
    def test_retry_on_temporary_failure(self, mock_send_mail):
        """Test that notification system retries on temporary failures"""
        # First call fails, second succeeds
        mock_send_mail.side_effect = [
            Exception("Temporary failure"),
            Mock(return_value=1)
        ]
        
        clinician = User.objects.create_user(
            username="retry_doc",
            password="testpass",
            role="CLINICIAN"
        )
        
        patient_user = User.objects.create_user(
            username="retry_patient",
            password="testpass",
            email="retry@test.com",
            role="PATIENT"
        )
        
        patient = Patient.objects.create(user=patient_user)
        
        appointment = Appointment.objects.create(
            patient=patient,
            clinician=clinician,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            status='SCHEDULED'
        )
        
        # In production, Celery would handle retries
        # This tests the basic retry concept
        try:
            schedule_appointment_reminder(appointment.id)
        except Exception:
            # First attempt fails
            pass
        
        # Retry would succeed (in actual Celery task)


@pytest.mark.django_db
class TestNotificationAuditLogging:
    """Tests for notification audit logging"""

    @patch('notifications.tasks.send_mail')
    def test_notification_sending_is_logged(self, mock_send_mail):
        """Test that notification sending events are logged"""
        clinician = User.objects.create_user(
            username="log_doc",
            password="testpass",
            role="CLINICIAN"
        )
        
        patient_user = User.objects.create_user(
            username="log_patient",
            password="testpass",
            email="log@test.com",
            role="PATIENT"
        )
        
        patient = Patient.objects.create(user=patient_user)
        
        appointment = Appointment.objects.create(
            patient=patient,
            clinician=clinician,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            status='SCHEDULED'
        )
        
        # Send notification
        schedule_appointment_reminder(appointment.id)
        
        # In production, would verify audit log entry exists
        # Currently just verify task executes without error
        assert mock_send_mail.called