import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from appointments.models import Appointment
from authentication.models import User
from patients.models import Patient


@pytest.mark.django_db
def test_specialty_search_and_closed_status_validation():
    doctor = User.objects.create_user(username='heart-doctor', role='CLINICIAN', specialty='Cardiology')
    User.objects.create_user(username='skin-doctor', role='CLINICIAN', specialty='Dermatology')
    patient = Patient.objects.create(user=User.objects.create_user(username='status-check', role='PATIENT'))
    appointment = Appointment.objects.create(patient=patient, clinician=doctor, appointment_date='2030-01-01', appointment_time='09:00', status='COMPLETED')
    client = APIClient()
    client.force_authenticate(doctor)
    result = client.get(reverse('clinician-search'), {'specialty': 'cardio'})
    assert [item['id'] for item in result.data] == [doctor.id]
    result = client.patch(reverse('appointment-status-update', kwargs={'appointment_id': appointment.appointment_id}), {'status': 'CANCELLED'}, format='json')
    assert result.status_code == 409


@pytest.mark.django_db
def test_report_rejects_invalid_date():
    admin = User.objects.create_user(username='report-admin', role='ADMIN')
    client = APIClient()
    client.force_authenticate(admin)
    assert client.post(reverse('patient-volume'), {'date': 'not-a-date'}, format='json').status_code == 400
