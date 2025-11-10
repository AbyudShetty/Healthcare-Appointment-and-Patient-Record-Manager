import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from authentication.models import User
from appointments.models import ClinicianSchedule, Appointment
from patients.models import Patient
from datetime import date, time


@pytest.mark.django_db
def test_available_slots_exclude_booked_slots():
    """Ensure booked slots are excluded from clinician availability."""
    client = APIClient()
    clinician = User.objects.create_user(username="doc", role="CLINICIAN", password="pass")
    patient_user = User.objects.create_user(username="pat", password="pass")
    patient = Patient.objects.create(user=patient_user, patient_id="P001")

    # Create one available slot
    ClinicianSchedule.objects.create(
        clinician=clinician,
        date=date.today(),
        start_time=time(10, 0),
        end_time=time(10, 30)
    )

    # Book that slot
    Appointment.objects.create(
        patient=patient,
        clinician=clinician,
        appointment_date=date.today(),
        appointment_time=time(10, 0),
        status="SCHEDULED"
    )

    client.force_authenticate(user=patient_user)
    url = reverse('clinician-availability', kwargs={'clinician_id': clinician.id})
    response = client.get(url, {'date': date.today().strftime("%Y-%m-%d")})

    assert response.status_code == 200
    assert len(response.data) == 0  # Booked slot excluded


@pytest.mark.django_db
def test_available_slots_return_when_not_booked():
    """Check that available slots are returned when none are booked."""
    client = APIClient()
    clinician = User.objects.create_user(username="doc2", role="CLINICIAN", password="pass")
    patient_user = User.objects.create_user(username="pat2", password="pass")
    patient = Patient.objects.create(user=patient_user)

    # Clinician has one available slot
    ClinicianSchedule.objects.create(
        clinician=clinician,
        date=date.today(),
        start_time=time(9, 0),
        end_time=time(9, 30)
    )

    client.force_authenticate(user=patient_user)
    url = reverse('clinician-availability', kwargs={'clinician_id': clinician.id})
    response = client.get(url, {'date': date.today().strftime("%Y-%m-%d")})

    assert response.status_code == 200
    assert len(response.data) == 1  # Slot available


@pytest.mark.django_db
def test_invalid_clinician_returns_404():
    """Ensure invalid clinician ID returns 404."""
    client = APIClient()
    user = User.objects.create_user(username="user", password="pass")
    client.force_authenticate(user=user)

    url = reverse('clinician-availability', kwargs={'clinician_id': 999})
    response = client.get(url, {'date': date.today().strftime("%Y-%m-%d")})

    assert response.status_code == 404


@pytest.mark.django_db
def test_missing_date_param_returns_400():
    """Ensure API returns 400 if date query param is missing."""
    client = APIClient()
    clinician = User.objects.create_user(username="doc3", role="CLINICIAN", password="pass")
    patient_user = User.objects.create_user(username="pat3", password="pass")
    patient = Patient.objects.create(user=patient_user)

    client.force_authenticate(user=patient_user)
    url = reverse('clinician-availability', kwargs={'clinician_id': clinician.id})
    response = client.get(url)  # Missing date

    assert response.status_code == 400
    assert "Missing 'date' parameter" in response.data["error"]