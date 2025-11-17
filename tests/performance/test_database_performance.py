import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from patients.models import Patient
from electronic_records.models import PatientRecord
from appointments.models import Appointment
import time
from rest_framework.test import APIRequestFactory, force_authenticate


User = get_user_model()

@pytest.mark.django_db
class TestDatabasePerformance:
    """Test database performance with 10,000 records (NF-004)"""
    
    @pytest.fixture(autouse=True)
    def setup_large_dataset(self, django_db_setup, django_db_blocker):
        """Create 10,000 patient records for testing"""
        with django_db_blocker.unblock():
            # Create users and patients in bulk
            users = []
            for i in range(10000):
                users.append(User(
                    username=f"patient_{i}",
                    email=f"patient_{i}@test.com",
                    role="PATIENT"
                ))
            
            User.objects.bulk_create(users, batch_size=1000)
            
            # Create patient profiles
            patients = []
            for user in User.objects.filter(role="PATIENT")[:10000]:
                patients.append(Patient(user=user))
            
            Patient.objects.bulk_create(patients, batch_size=1000)
    
    def test_patient_search_performance(self):
        """Ensure patient search completes within 7 seconds (F-015)"""
        from electronic_records.views import PatientRecordSearchView
        from rest_framework.test import APIRequestFactory
        from rest_framework.test import force_authenticate
        
        factory = APIRequestFactory()
        clinician = User.objects.create_user(
            username="test_clinician",
            role="CLINICIAN"
        )
        
        request = factory.get('/api/v1/records/search/?q=patient')
        force_authenticate(request, user=clinician)
        
        view = PatientRecordSearchView.as_view()
        
        start_time = time.time()
        response = view(request)
        duration = time.time() - start_time
        
        assert duration <= 7.0, f"Search took {duration:.2f}s, exceeds 7s limit"
        assert response.status_code == 200
    
    def test_record_retrieval_performance(self):
        """Ensure record view loads within 5 seconds (NF-002)"""
        patient = Patient.objects.first()
        
        # Create record
        record = PatientRecord.objects.create(
            patient=patient,
            medical_history_encrypted="Test history"
        )
        
        start_time = time.time()
        retrieved = PatientRecord.objects.select_related('patient__user').get(id=record.id)
        duration = time.time() - start_time
        
        assert duration <= 5.0, f"Record retrieval took {duration:.2f}s"
        assert retrieved.id == record.id
    
    def test_appointment_booking_performance(self):
        """Ensure appointment booking completes within 10 seconds (NF-001)"""
        from appointments.views import AppointmentBookingView
        from rest_framework.test import APIRequestFactory
        from datetime import date, time as dtime
        
        factory = APIRequestFactory()
        patient = Patient.objects.first()
        clinician = User.objects.create_user(
            username="booking_clinician",
            role="CLINICIAN"
        )
        
        request = factory.post('/api/v1/appointments/book/', {
            'patient': patient.id,
            'clinician': clinician.id,
            'appointment_date': date.today().strftime('%Y-%m-%d'),
            'appointment_time': dtime(14, 0).strftime('%H:%M:%S'),
            'reason_for_visit': 'Performance test'
        })
        force_authenticate(request, user=patient.user)
        
        view = AppointmentBookingView.as_view()
        
        start_time = time.time()
        response = view(request)
        duration = time.time() - start_time
        
        assert duration <= 10.0, f"Booking took {duration:.2f}s, exceeds 10s limit"