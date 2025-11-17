import pytest
from django.contrib.auth import get_user_model
from patients.models import Patient

User = get_user_model()

@pytest.mark.django_db
class TestPatientRegistration:
    """Unit tests for patient registration (HCRM-F-001)"""
    
    def test_patient_registration_success(self):
        """Test successful patient registration with unique ID"""
        user_data = {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'SecurePass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '1234567890',
            'role': 'PATIENT'
        }
        user = User.objects.create_user(**user_data)
        patient = Patient.objects.create(user=user)
        
        assert patient.patient_id.startswith('PAT')
        assert len(patient.patient_id) == 9
        assert Patient.objects.count() >= 1
    
    def test_patient_id_uniqueness(self):
        """Test that patient IDs are unique and sequential"""
        user1 = User.objects.create_user(username='user1', email='user1@example.com')
        user2 = User.objects.create_user(username='user2', email='user2@example.com')
        
        patient1 = Patient.objects.create(user=user1)
        patient2 = Patient.objects.create(user=user2)
        
        assert patient1.patient_id != patient2.patient_id
        assert int(patient2.patient_id[3:]) == int(patient1.patient_id[3:]) + 1
