from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from authentication.models import User
from electronic_records.models import ClinicalNote, PatientRecord
from patients.models import Patient


@pytest.mark.django_db
def test_record_fields_round_trip_and_legacy_bytes_literal():
    clinician = User.objects.create_user(username='record-doctor', password='password', role='CLINICIAN')
    patient_user = User.objects.create_user(username='record-patient', password='password')
    patient = Patient.objects.create(user=patient_user)
    client = APIClient()
    client.force_authenticate(clinician)
    response = client.post(reverse('record-quick-create'), {
        'patient_id': patient.patient_id, 'medical_history': 'history',
        'diagnoses': 'diagnosis', 'medications': 'medicine',
    }, format='json')
    assert response.status_code == 201
    record = PatientRecord.objects.get(patient=patient)
    assert response.data['medical_history'] == 'history'
    assert response.data['diagnoses'] == 'diagnosis'
    assert response.data['medications'] == 'medicine'
    assert record.medical_history_encrypted != 'history'
    record.medical_history_encrypted = repr(record.medical_history_encrypted.encode())
    record.save()
    assert PatientRecord.objects.get(pk=record.pk).medical_history == 'history'


@pytest.mark.django_db
def test_note_encryption_failure_does_not_save_plaintext():
    patient_user = User.objects.create_user(username='note-patient', password='password')
    patient = Patient.objects.create(user=patient_user)
    record = PatientRecord.objects.create(patient=patient)
    with patch('electronic_records.models.encrypt_field', side_effect=RuntimeError('key unavailable')):
        with pytest.raises(RuntimeError):
            ClinicalNote.objects.create(record=record, note_content_encrypted='private')
    assert not ClinicalNote.objects.filter(record=record).exists()
