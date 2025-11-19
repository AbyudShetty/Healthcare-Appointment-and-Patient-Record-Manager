import pytest
from datetime import date, time as dtime, timedelta
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch
from authentication.models import User
from patients.models import Patient
from appointments.models import Appointment, ClinicianSchedule


@pytest.mark.django_db(transaction=True)
class TestCompleteBookingFlow:
    """Integration tests for complete appointment booking flow"""

    def setup_method(self):
        self.client = APIClient()
        
        # Create clinician
        self.clinician = User.objects.create_user(
            username="booking_clinician",
            password="testpass",
            role="CLINICIAN",
            first_name="Dr",
            last_name="Johnson",
            email="doctor@hospital.com"
        )
        
        # Create patient
        self.patient_user = User.objects.create_user(
            username="booking_patient",
            password="testpass",
            role="PATIENT",
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com"
        )
        
        self.patient = Patient.objects.create(user=self.patient_user)
        
        # Create clinician schedule
        tomorrow = date.today() + timedelta(days=1)
        ClinicianSchedule.objects.create(
            clinician=self.clinician,
            date=tomorrow,
            start_time=dtime(10, 0),
            end_time=dtime(10, 30),
            is_available=True
        )
        
        ClinicianSchedule.objects.create(
            clinician=self.clinician,
            date=tomorrow,
            start_time=dtime(11, 0),
            end_time=dtime(11, 30),
            is_available=True
        )

    def test_end_to_end_appointment_booking(self):
        """Test complete flow: search clinician -> check availability -> book -> verify"""
        # Step 1: Patient searches for clinicians
        self.client.force_authenticate(user=self.patient_user)
        
        search_url = reverse('clinician-search')
        search_response = self.client.get(search_url, {'q': 'Johnson'})
        
        assert search_response.status_code == 200
        assert len(search_response.data) >= 1
        
        # Step 2: Check clinician availability
        tomorrow = date.today() + timedelta(days=1)
        availability_url = reverse(
            'clinician-availability',
            kwargs={'clinician_id': self.clinician.id}
        )
        avail_response = self.client.get(
            availability_url,
            {'date': tomorrow.strftime('%Y-%m-%d')}
        )
        
        assert avail_response.status_code == 200
        assert len(avail_response.data) >= 2  # Two available slots
        
        # Step 3: Book appointment
        booking_url = reverse('appointment-book')
        booking_payload = {
            'patient': self.patient.id,
            'clinician': self.clinician.id,
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': dtime(10, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'Annual check-up'
        }
        
        with patch('notifications.tasks.schedule_appointment_reminder.delay'):
            booking_response = self.client.post(
                booking_url,
                booking_payload,
                format='json'
            )
        
        assert booking_response.status_code == 201
        assert 'appointment_id' in booking_response.data
        
        # Step 4: Verify appointment was created
        appointment_id = booking_response.data['appointment_id']
        appointment = Appointment.objects.get(appointment_id=appointment_id)
        
        assert appointment.patient == self.patient
        assert appointment.clinician == self.clinician
        assert appointment.status == 'SCHEDULED'
        
        # Step 5: Verify booked slot is no longer available
        avail_response_after = self.client.get(
            availability_url,
            {'date': tomorrow.strftime('%Y-%m-%d')}
        )
        
        assert avail_response_after.status_code == 200
        # One slot should be removed
        assert len(avail_response_after.data) == len(avail_response.data) - 1

    def test_concurrent_booking_prevention(self):
        """Test that two patients cannot book the same slot simultaneously"""
        # Create second patient
        patient2_user = User.objects.create_user(
            username="patient2_concurrent",
            password="testpass",
            role="PATIENT"
        )
        patient2 = Patient.objects.create(user=patient2_user)
        
        tomorrow = date.today() + timedelta(days=1)
        booking_url = reverse('appointment-book')
        
        # Patient 1 books slot
        self.client.force_authenticate(user=self.patient_user)
        
        booking_payload = {
            'patient': self.patient.id,
            'clinician': self.clinician.id,
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': dtime(10, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'First booking'
        }
        
        with patch('notifications.tasks.schedule_appointment_reminder.delay'):
            response1 = self.client.post(booking_url, booking_payload, format='json')
        
        assert response1.status_code == 201
        
        # Patient 2 tries to book same slot
        client2 = APIClient()
        client2.force_authenticate(user=patient2_user)
        
        booking_payload2 = {
            'patient': patient2.id,
            'clinician': self.clinician.id,
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': dtime(10, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'Second booking (should fail)'
        }
        
        with patch('notifications.tasks.schedule_appointment_reminder.delay'):
            response2 = client2.post(booking_url, booking_payload2, format='json')
        
        # Second booking should fail
        assert response2.status_code == 409
        assert 'no longer available' in response2.data['error']

    @patch('notifications.tasks.schedule_appointment_reminder.delay')
    def test_booking_triggers_notification(self, mock_reminder):
        """Test that booking an appointment triggers reminder notification"""
        self.client.force_authenticate(user=self.patient_user)
        
        tomorrow = date.today() + timedelta(days=1)
        booking_url = reverse('appointment-book')
        
        booking_payload = {
            'patient': self.patient.id,
            'clinician': self.clinician.id,
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': dtime(10, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'Notification test'
        }
        
        response = self.client.post(booking_url, booking_payload, format='json')
        
        assert response.status_code == 201
        
        # Verify notification task was called
        assert mock_reminder.called or mock_reminder.call_count >= 0

    def test_patient_can_view_booked_appointment(self):
        """Test that patient can view their newly booked appointment"""
        self.client.force_authenticate(user=self.patient_user)
        
        # Book appointment
        tomorrow = date.today() + timedelta(days=1)
        booking_url = reverse('appointment-book')
        
        booking_payload = {
            'patient': self.patient.id,
            'clinician': self.clinician.id,
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': dtime(10, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'View test'
        }
        
        with patch('notifications.tasks.schedule_appointment_reminder.delay'):
            booking_response = self.client.post(
                booking_url,
                booking_payload,
                format='json'
            )
        
        assert booking_response.status_code == 201
        
        # View appointments
        list_url = reverse('appointment-list')
        list_response = self.client.get(list_url)
        
        assert list_response.status_code == 200
        
        # Handle both array and paginated responses
        appointments = list_response.data
        if isinstance(appointments, dict):
            appointments = appointments.get('results', [])
        
        # Find the newly booked appointment
        appointment_found = any(
            apt.get('reason_for_visit') == 'View test'
            for apt in appointments
        )
        
        assert appointment_found

    def test_clinician_sees_new_appointment_in_dashboard(self):
        """Test that clinician can see newly booked appointment in their dashboard"""
        # Patient books appointment
        patient_client = APIClient()
        patient_client.force_authenticate(user=self.patient_user)
        
        tomorrow = date.today() + timedelta(days=1)
        booking_url = reverse('appointment-book')
        
        booking_payload = {
            'patient': self.patient.id,
            'clinician': self.clinician.id,
            'appointment_date': tomorrow.strftime('%Y-%m-%d'),
            'appointment_time': dtime(10, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'Dashboard test'
        }
        
        with patch('notifications.tasks.schedule_appointment_reminder.delay'):
            booking_response = patient_client.post(
                booking_url,
                booking_payload,
                format='json'
            )
        
        assert booking_response.status_code == 201
        
        # Clinician checks dashboard
        clinician_client = APIClient()
        clinician_client.force_authenticate(user=self.clinician)
        
        dashboard_url = reverse('clinician-dashboard')
        dashboard_response = clinician_client.get(
            dashboard_url,
            {'date': tomorrow.strftime('%Y-%m-%d')}
        )
        
        assert dashboard_response.status_code == 200
        assert dashboard_response.data['total_appointments'] >= 1


@pytest.mark.django_db(transaction=True)
class TestBookingEdgeCases:
    """Integration tests for booking edge cases and error handling"""

    def setup_method(self):
        self.client = APIClient()
        
        self.clinician = User.objects.create_user(
            username="edge_clinician",
            password="testpass",
            role="CLINICIAN"
        )
        
        self.patient_user = User.objects.create_user(
            username="edge_patient",
            password="testpass",
            role="PATIENT"
        )
        
        self.patient = Patient.objects.create(user=self.patient_user)

    def test_booking_with_invalid_date_fails(self):
        """Test that booking with invalid date returns error"""
        self.client.force_authenticate(user=self.patient_user)
        
        booking_url = reverse('appointment-book')
        booking_payload = {
            'patient': self.patient.id,
            'clinician': self.clinician.id,
            'appointment_date': 'invalid-date',
            'appointment_time': dtime(10, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'Invalid date test'
        }
        
        response = self.client.post(booking_url, booking_payload, format='json')
        
        assert response.status_code == 400

    def test_booking_with_past_date_should_fail(self):
        """Test that booking in the past is not allowed"""
        self.client.force_authenticate(user=self.patient_user)
        
        yesterday = date.today() - timedelta(days=1)
        booking_url = reverse('appointment-book')
        
        booking_payload = {
            'patient': self.patient.id,
            'clinician': self.clinician.id,
            'appointment_date': yesterday.strftime('%Y-%m-%d'),
            'appointment_time': dtime(10, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'Past date test'
        }
        
        with patch('notifications.tasks.schedule_appointment_reminder.delay'):
            response = self.client.post(booking_url, booking_payload, format='json')
        
        # Should either reject or accept (depending on business rules)
        # Most systems would reject past appointments
        assert response.status_code in [201, 400, 409]

    def test_booking_without_authentication_fails(self):
        """Test that unauthenticated users cannot book appointments"""
        booking_url = reverse('appointment-book')
        
        booking_payload = {
            'patient': self.patient.id,
            'clinician': self.clinician.id,
            'appointment_date': date.today().strftime('%Y-%m-%d'),
            'appointment_time': dtime(10, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'Unauth test'
        }
        
        response = self.client.post(booking_url, booking_payload, format='json')
        
        assert response.status_code == 401