from datetime import timedelta, time, datetime
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment, ClinicianSchedule
from authentication.models import User
from notifications.tasks import schedule_appointment_reminder
from patients.models import Patient


@pytest.mark.django_db
def test_booking_schedules_reminder_and_cancelled_appointments_are_skipped():
    doctor = User.objects.create_user(username='reminder-doctor', role='CLINICIAN')
    user = User.objects.create_user(username='reminder-patient', role='PATIENT')
    patient = Patient.objects.create(user=user)
    day = timezone.localdate() + timedelta(days=3)
    ClinicianSchedule.objects.create(clinician=doctor, date=day, start_time=time(9), end_time=time(9, 30))
    client = APIClient()
    client.force_authenticate(user)
    with patch('notifications.tasks.schedule_appointment_reminder.apply_async') as enqueue:
        response = client.post(reverse('appointment-book'), {'patient': patient.pk, 'clinician': doctor.pk,
                               'appointment_date': day.isoformat(), 'appointment_time': '09:00'}, format='json')
    assert response.status_code == 201
    assert enqueue.call_args.kwargs['eta'] == timezone.make_aware(datetime.combine(day, time(9))) - timedelta(days=1)
    appointment = Appointment.objects.get(appointment_id=response.data['appointment_id'])
    appointment.status = 'CANCELLED'
    appointment.save()
    with patch('notifications.tasks.send_mail') as send:
        schedule_appointment_reminder(appointment.pk)
    send.assert_not_called()
