import pytest
from rest_framework.test import APIClient
from authentication.models import User
from patients.models import Patient
from electronic_records.models import PatientRecord

@pytest.mark.django_db
class TestPatientRecordSearch:
    """Tests for Fast Search & Filter (F-015)"""

    def setup_method(self):
        self.client = APIClient()
        self.clinician = User.objects.create_user(
            username='clinician1',
            password='pass123',
            role='CLINICIAN'
        )
        self.patient_user = User.objects.create_user(
            username='patient1',
            password='pass123',
            first_name='John',
            last_name='Doe',
            role='PATIENT'
        )
        self.patient = Patient.objects.create(user=self.patient_user)
        PatientRecord.objects.create(
            patient=self.patient,
            medical_history_encrypted='History: Diabetes',
            diagnoses_encrypted='Diabetes Mellitus',
            medications_encrypted='Metformin',
            created_by=self.clinician
        )
        self.client.force_authenticate(user=self.clinician)

    def test_search_by_patient_name(self):
        """Clinician should find a record by patient name"""
        response = self.client.get('/api/v1/records/search/?q=John')
        assert response.status_code == 200
        assert response.data['count'] >= 1
        assert response.data['results'][0]['diagnoses'] == 'Diabetes Mellitus'

    def test_search_returns_empty_for_unauthorized_user(self):
        """Patients should not be able to search records"""
        unauthorized = User.objects.create_user(
            username='patient2',
            password='pass123',
            role='PATIENT'
        )
        self.client.force_authenticate(user=unauthorized)
        response = self.client.get('/api/v1/records/search/?q=John')
        assert response.status_code == 200
        assert response.data['count'] == 0
        assert response.data['results'] == []
