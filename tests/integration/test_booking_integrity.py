from concurrent.futures import ThreadPoolExecutor
from datetime import date, time, timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections
from django.urls import reverse
from rest_framework.test import APIClient

from appointments.models import Appointment, ClinicianSchedule
from authentication.models import User
from patients.models import Patient


@pytest.mark.django_db(transaction=True)
def test_concurrent_bookings_only_create_one_appointment():
    doctor = User.objects.create_user(username='race-doctor', role='CLINICIAN')
    users = [User.objects.create_user(username=f'race-{i}', role='PATIENT') for i in range(2)]
    patients = [Patient.objects.create(user=user) for user in users]
    day = date.today() + timedelta(days=1)
    ClinicianSchedule.objects.create(clinician=doctor, date=day, start_time=time(9), end_time=time(9, 30))
    barrier = Barrier(2)

    def book(index):
        close_old_connections()
        client = APIClient()
        client.force_authenticate(user=users[index])
        barrier.wait(timeout=10)
        result = client.post(reverse('appointment-book'), {
            'patient': patients[index].pk, 'clinician': doctor.pk,
            'appointment_date': day.isoformat(), 'appointment_time': '09:00',
        }, format='json')
        close_old_connections()
        return result.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(book, range(2)))
    assert sorted(statuses) == [201, 409]
    assert Appointment.objects.filter(clinician=doctor, appointment_date=day).count() == 1
