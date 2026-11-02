import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from appointments.models import Appointment
from authentication.models import User
from patients.models import Patient


@pytest.mark.django_db
def test_patient_cannot_book_for_another_patient():
    actor = User.objects.create_user(username='booking-actor', password='password', role='PATIENT')
    other = Patient.objects.create(user=User.objects.create_user(username='booking-other', password='password'))
    doctor = User.objects.create_user(username='booking-doctor', password='password', role='CLINICIAN')
    client = APIClient()
    client.force_authenticate(actor)
    response = client.post(reverse('appointment-book'), {
        'patient': other.pk, 'clinician': doctor.pk,
        'appointment_date': '2030-01-01', 'appointment_time': '09:00',
    }, format='json')
    assert response.status_code == 403
    assert not Appointment.objects.exists()


@pytest.mark.django_db
def test_clinician_cannot_update_another_clinicians_appointment():
    doctor = User.objects.create_user(username='owner-doctor', password='password', role='CLINICIAN')
    other = User.objects.create_user(username='other-doctor', password='password', role='CLINICIAN')
    patient = Patient.objects.create(user=User.objects.create_user(username='status-patient', password='password'))
    appointment = Appointment.objects.create(patient=patient, clinician=doctor, appointment_date='2030-01-01', appointment_time='09:00')
    client = APIClient()
    client.force_authenticate(other)
    response = client.patch(reverse('appointment-status-update', kwargs={'appointment_id': appointment.appointment_id}), {'status': 'CANCELLED'}, format='json')
    assert response.status_code == 403
    appointment.refresh_from_db()
    assert appointment.status == 'SCHEDULED'
