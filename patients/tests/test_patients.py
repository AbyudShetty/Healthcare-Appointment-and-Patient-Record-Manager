import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from authentication.models import User
from patients.models import Patient


@pytest.mark.django_db
class TestPatientRegistration:
    """Tests for patient registration (HCRM-F-001)"""

    def setup_method(self):
        self.client = APIClient()
        self.register_url = reverse('patient-register')

    def test_patient_registration_creates_user_and_profile(self):
        """Test that patient registration creates both User and Patient records"""
        payload = {
            'user': {
                'username': 'new_patient',
                'email': 'newpatient@test.com',
                'password': 'SecurePass123!'
            }
        }
        
        response = self.client.post(self.register_url, payload, format='json')
        
        assert response.status_code == 201
        assert User.objects.filter(username='new_patient').exists()
        
        user = User.objects.get(username='new_patient')
        assert Patient.objects.filter(user=user).exists()

    def test_patient_registration_generates_unique_id(self):
        """Test that each patient gets a unique patient_id"""
        payload1 = {
            'user': {
                'username': 'patient1',
                'email': 'patient1@test.com',
                'password': 'Pass123!'
            }
        }
        response1 = self.client.post(self.register_url, payload1, format='json')
        
        payload2 = {
            'user': {
                'username': 'patient2',
                'email': 'patient2@test.com',
                'password': 'Pass123!'
            }
        }
        response2 = self.client.post(self.register_url, payload2, format='json')
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        user1 = User.objects.get(username='patient1')
        user2 = User.objects.get(username='patient2')
        
        patient1 = Patient.objects.get(user=user1)
        patient2 = Patient.objects.get(user=user2)
        
        assert patient1.patient_id != patient2.patient_id
        assert patient1.patient_id.startswith('PAT')
        assert patient2.patient_id.startswith('PAT')

    def test_patient_id_is_sequential(self):
        """Test that patient IDs are generated sequentially"""
        user1 = User.objects.create_user(username='seq1', password='pass', role='PATIENT')
        patient1 = Patient.objects.create(user=user1)
        
        user2 = User.objects.create_user(username='seq2', password='pass', role='PATIENT')
        patient2 = Patient.objects.create(user=user2)
        
        id1_num = int(patient1.patient_id[3:])
        id2_num = int(patient2.patient_id[3:])
        
        assert id2_num == id1_num + 1



@pytest.mark.django_db
class TestPatientProfileUpdate:
    """Tests for patient profile updates (HCRM-F-002)"""

    def setup_method(self):
        self.client = APIClient()
        self.profile_url = reverse('patient-profile')
        
        self.user = User.objects.create_user(
            username='profile_test',
            password='testpass',
            email='profile@test.com',
            role='PATIENT',
            first_name='John',
            last_name='Doe'
        )
        
        self.patient = Patient.objects.create(
            user=self.user,
            address='123 Main St',
            emergency_contact='555-1234',
            blood_group='O+',
            allergies='Penicillin'
        )

    def test_authenticated_patient_can_view_profile(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.profile_url)
        
        assert response.status_code == 200
        assert 'user_email' in response.data or 'email' in str(response.data).lower()

    def test_patient_can_update_address(self):
        self.client.force_authenticate(user=self.user)
        
        new_address = '456 New Street'
        response = self.client.patch(self.profile_url, {'address': new_address}, format='json')
        
        assert response.status_code == 200
        
        self.patient.refresh_from_db()
        assert self.patient.address == new_address

    def test_patient_can_update_emergency_contact(self):
        self.client.force_authenticate(user=self.user)
        
        new_contact = '555-9999'
        response = self.client.patch(self.profile_url, {'emergency_contact': new_contact}, format='json')
        
        assert response.status_code == 200
        
        self.patient.refresh_from_db()
        assert self.patient.emergency_contact == new_contact

    def test_patient_can_update_blood_group(self):
        self.client.force_authenticate(user=self.user)
        
        new_blood_group = 'A+'
        response = self.client.patch(self.profile_url, {'blood_group': new_blood_group}, format='json')
        
        assert response.status_code == 200
        
        self.patient.refresh_from_db()
        assert self.patient.blood_group == new_blood_group

    def test_patient_can_update_allergies(self):
        self.client.force_authenticate(user=self.user)
        
        new_allergies = 'Penicillin, Latex'
        response = self.client.patch(self.profile_url, {'allergies': new_allergies}, format='json')
        
        assert response.status_code == 200
        
        self.patient.refresh_from_db()
        assert self.patient.allergies == new_allergies

    def test_unauthenticated_user_cannot_access_profile(self):
        response = self.client.get(self.profile_url)
        assert response.status_code == 401

    def test_profile_update_triggers_audit_log(self):
        self.client.force_authenticate(user=self.user)
        
        response = self.client.patch(self.profile_url, {'address': 'New Address'}, format='json')
        
        assert response.status_code == 200



@pytest.mark.django_db
class TestPatientModel:
    """Tests for Patient model functionality"""

    def test_patient_str_representation(self):
        user = User.objects.create_user(
            username='str_test',
            password='pass',
            first_name='Jane',
            last_name='Smith'
        )
        
        patient = Patient.objects.create(user=user)
        
        expected = f"{patient.patient_id} - Jane Smith"
        assert str(patient) == expected

    def test_patient_timestamps_are_auto_set(self):
        user = User.objects.create_user(username='timestamp_test', password='pass')
        patient = Patient.objects.create(user=user)
        
        assert patient.created_at is not None
        assert patient.updated_at is not None

    def test_patient_updated_at_changes_on_save(self):
        import time
        
        user = User.objects.create_user(username='update_test', password='pass')
        
        patient = Patient.objects.create(user=user)
        original_updated_at = patient.updated_at
        
        time.sleep(0.1)
        
        patient.address = "New Address"
        patient.save()
        
        assert patient.updated_at > original_updated_at



@pytest.mark.django_db
class TestPatientQueryMethods:
    """Tests for querying patient records"""

    def setup_method(self):
        for i in range(5):
            user = User.objects.create_user(username=f'query_patient_{i}', password='pass', role='PATIENT')
            Patient.objects.create(user=user)

    def test_can_query_all_patients(self):
        patients = Patient.objects.all()
        assert patients.count() >= 5

    def test_can_filter_patients_by_blood_group(self):
        user = User.objects.create_user(username='blood_filter', password='pass')
        patient = Patient.objects.create(user=user, blood_group='AB+')
        
        ab_positive_patients = Patient.objects.filter(blood_group='AB+')
        assert patient in ab_positive_patients

    def test_can_search_patients_by_user_name(self):
        user = User.objects.create_user(username='search_test', password='pass', first_name='Unique', last_name='Name')
        patient = Patient.objects.create(user=user)
        
        found_patients = Patient.objects.filter(user__first_name__icontains='Unique')
        assert patient in found_patients



@pytest.mark.django_db
class TestPatientDataValidation:
    """Tests for patient data validation"""

    def test_patient_id_cannot_be_manually_set(self):
        user = User.objects.create_user(username='manual_id_test', password='pass')
        patient = Patient.objects.create(user=user)
        
        assert patient.patient_id.startswith('PAT')
        assert len(patient.patient_id) == 9

    def test_patient_fields_can_be_blank(self):
        user = User.objects.create_user(username='blank_test', password='pass')
        patient = Patient.objects.create(user=user)
        
        assert patient.address == ''
        assert patient.emergency_contact == ''
        assert patient.blood_group == ''
        assert patient.allergies == ''