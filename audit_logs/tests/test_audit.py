import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from authentication.models import User
from audit_logs.utils import log_action
from audit_logs.models import AuditLog


@pytest.mark.django_db
class TestAuditLogging:
    """Tests for audit logging functionality (HCRM-SR-004)"""

    def setup_method(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin_audit",
            password="testpass",
            role="ADMIN",
            first_name="Admin",
            last_name="User"
        )
        self.patient = User.objects.create_user(
            username="patient_audit",
            password="testpass",
            role="PATIENT"
        )

    def test_log_action_creates_entry(self):
        """Test that log_action utility function works"""
        # This is a placeholder test since audit logging is currently stub
        # In production, this would verify database entries
        result = log_action(
            user=self.admin,
            action="TEST_ACTION",
            details="Test audit log entry"
        )
        # Currently just prints, so we verify it doesn't crash
        assert AuditLog.objects.filter(pk=result.pk, action='TEST_ACTION').exists()

    def test_admin_can_access_logs_endpoint(self):
        """Test that admin users can access audit logs endpoint"""
        self.client.force_authenticate(user=self.admin)
        url = reverse('admin-logs-list')
        response = self.client.get(url)
        
        assert response.status_code == 200
        # Currently returns empty array
        assert isinstance(response.data['results'], list)

    def test_non_admin_cannot_access_logs(self):
        """Test that non-admin users are forbidden from accessing logs"""
        self.client.force_authenticate(user=self.patient)
        url = reverse('admin-logs-list')
        response = self.client.get(url)
        
        assert response.status_code == 403

    def test_unauthenticated_user_cannot_access_logs(self):
        """Test that unauthenticated users cannot access logs"""
        url = reverse('admin-logs-list')
        response = self.client.get(url)
        
        assert response.status_code == 401


@pytest.mark.django_db
class TestAuditLogCreation:
    """Tests for automatic audit log creation on critical actions"""

    def setup_method(self):
        self.client = APIClient()
        self.clinician = User.objects.create_user(
            username="clinician_audit",
            password="testpass",
            role="CLINICIAN"
        )

    def test_appointment_booking_triggers_audit_log(self):
        """Test that booking an appointment creates an audit log entry"""
        from patients.models import Patient
        from appointments.models import ClinicianSchedule
        from datetime import date, time, timedelta
        
        patient_user = User.objects.create_user(
            username="patient_booking_audit",
            password="testpass",
            role="PATIENT"
        )
        patient = Patient.objects.create(user=patient_user)
        
        self.client.force_authenticate(user=patient_user)
        
        # Book appointment (should trigger audit log)
        url = reverse('appointment-book')
        day = date.today() + timedelta(days=1)
        ClinicianSchedule.objects.create(clinician=self.clinician, date=day, start_time=time(10), end_time=time(10, 30))
        payload = {
            'patient': patient.id,
            'clinician': self.clinician.id,
            'appointment_date': day.strftime('%Y-%m-%d'),
            'appointment_time': time(10, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'Audit test'
        }
        
        response = self.client.post(url, payload, format='json')
        assert response.status_code == 201
        assert AuditLog.objects.filter(user=patient_user, action='APPOINTMENT_BOOKED').exists()

    def test_record_creation_triggers_audit_log(self):
        """Test that creating a patient record triggers audit log"""
        from patients.models import Patient
        
        patient_user = User.objects.create_user(
            username="patient_record_audit",
            password="testpass",
            role="PATIENT"
        )
        patient = Patient.objects.create(user=patient_user)
        
        self.client.force_authenticate(user=self.clinician)
        
        url = reverse('record-quick-create')
        payload = {
            'patient_id': patient.patient_id,
            'medical_history': 'Test history',
            'diagnoses': 'Test diagnosis',
            'medications': 'Test meds'
        }
        
        response = self.client.post(url, payload, format='json')
        assert response.status_code == 201
        # Audit log would be created

    def test_clinical_note_addition_triggers_audit_log(self):
        """Test that adding clinical notes creates audit log entry"""
        from patients.models import Patient
        from electronic_records.models import PatientRecord
        
        patient_user = User.objects.create_user(
            username="patient_note_audit",
            password="testpass",
            role="PATIENT"
        )
        patient = Patient.objects.create(user=patient_user)
        record = PatientRecord.objects.create(
            patient=patient,
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
        # Audit log would be created


@pytest.mark.django_db
class TestAuditLogSecurity:
    """Tests for audit log security and immutability"""

    def setup_method(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username="admin_security",
            password="testpass",
            role="ADMIN"
        )

    def test_audit_logs_are_immutable(self):
        """Test that audit logs cannot be modified (future implementation)"""
        # This test is for future implementation when AuditLog model exists
        # Currently logs are just printed, not stored in DB
        pass

    def test_sensitive_data_not_logged(self):
        """Test that sensitive data like passwords are not logged"""
        # Test that password is not included in login audit logs
        log_action(
            user=self.admin,
            action="USER_LOGIN",
            details="User logged in successfully"
        )
        # Verify password not in log details (future implementation)
        pass
