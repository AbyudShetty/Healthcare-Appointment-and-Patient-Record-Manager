from datetime import timedelta, time, datetime
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment, ClinicianSchedule
from authentication.models import User
from notifications.tasks import schedule_appointment_reminder
from notifications.models import ReminderJob
from notifications.worker import process_one_reminder
from patients.models import Patient
from django.apps import apps
from django.db import connection


@pytest.mark.django_db
def test_booking_schedules_reminder_and_cancelled_appointments_are_skipped():
    doctor = User.objects.create_user(username='reminder-doctor', role='CLINICIAN')
    user = User.objects.create_user(username='reminder-patient', role='PATIENT')
    patient = Patient.objects.create(user=user)
    day = timezone.localdate() + timedelta(days=3)
    ClinicianSchedule.objects.create(clinician=doctor, date=day, start_time=time(9), end_time=time(9, 30))
    client = APIClient()
    client.force_authenticate(user)
    response = client.post(reverse('appointment-book'), {'patient': patient.pk, 'clinician': doctor.pk,
                           'appointment_date': day.isoformat(), 'appointment_time': '09:00'}, format='json')
    assert response.status_code == 201
    appointment = Appointment.objects.get(appointment_id=response.data['appointment_id'])
    job = ReminderJob.objects.get(appointment=appointment)
    assert job.due_at == timezone.make_aware(datetime.combine(day, time(9))) - timedelta(days=1)
    appointment.status = 'CANCELLED'
    appointment.save()
    with patch('notifications.tasks.send_mail') as send:
        schedule_appointment_reminder(appointment.pk)
    send.assert_not_called()


@pytest.mark.django_db
def test_failed_reminder_is_retried_and_only_sent_once():
    doctor = User.objects.create_user(username='worker-doctor', role='CLINICIAN')
    user = User.objects.create_user(username='worker-patient', role='PATIENT', email='worker@example.com')
    patient = Patient.objects.create(user=user)
    appointment = Appointment.objects.create(patient=patient, clinician=doctor, appointment_date=timezone.localdate(), appointment_time=time(9))
    job = ReminderJob.objects.create(appointment=appointment, due_at=timezone.now() - timedelta(seconds=1))
    with patch('notifications.tasks.send_mail', side_effect=OSError('unavailable')):
        assert process_one_reminder()
    job.refresh_from_db()
    assert job.state == 'PENDING' and job.attempts == 1
    job.due_at = timezone.now() - timedelta(seconds=1)
    job.save()
    with patch('notifications.tasks.send_mail') as send:
        assert process_one_reminder()
        assert not process_one_reminder()
    send.assert_called_once()
    job.refresh_from_db()
    assert job.state == 'SENT' and job.attempts == 2


@pytest.mark.django_db
def test_expired_final_lease_fails_and_is_visible_only_to_admin():
    doctor = User.objects.create_user(username='lease-doctor', role='CLINICIAN')
    user = User.objects.create_user(username='lease-patient', role='PATIENT')
    admin = User.objects.create_user(username='lease-admin', role='ADMIN')
    patient = Patient.objects.create(user=user)
    appointment = Appointment.objects.create(patient=patient, clinician=doctor, appointment_date=timezone.localdate(), appointment_time=time(9))
    job = ReminderJob.objects.create(appointment=appointment, due_at=timezone.now(), state='RUNNING', attempts=5,
                                     locked_until=timezone.now() - timedelta(seconds=1))
    assert process_one_reminder()
    job.refresh_from_db()
    assert job.state == 'FAILED'
    client = APIClient()
    client.force_authenticate(user)
    assert client.get(reverse('failed-reminders')).status_code == 403
    client.force_authenticate(admin)
    assert client.get(reverse('failed-reminders')).data['count'] == 1


@pytest.mark.django_db
def test_reschedule_replaces_pending_reminder_and_rejects_other_patient():
    doctor = User.objects.create_user(username='move-doctor', role='CLINICIAN')
    owner = User.objects.create_user(username='move-patient', role='PATIENT')
    other = User.objects.create_user(username='move-other', role='PATIENT')
    patient = Patient.objects.create(user=owner)
    day = timezone.localdate() + timedelta(days=3)
    new_day = day + timedelta(days=1)
    appointment = Appointment.objects.create(patient=patient, clinician=doctor, appointment_date=day, appointment_time=time(9))
    job = ReminderJob.objects.create(appointment=appointment, due_at=timezone.now(), state='RUNNING', claim_token='old')
    ClinicianSchedule.objects.create(clinician=doctor, date=new_day, start_time=time(10), end_time=time(10, 30))
    client = APIClient()
    client.force_authenticate(other)
    url = reverse('appointment-reschedule', kwargs={'appointment_id': appointment.appointment_id})
    payload = {'appointment_date': new_day.isoformat(), 'appointment_time': '10:00'}
    assert client.patch(url, payload, format='json').status_code == 403
    client.force_authenticate(owner)
    assert client.patch(url, payload, format='json').status_code == 200
    job.refresh_from_db()
    assert job.state == 'PENDING' and job.claim_token == ''
    assert job.due_at == timezone.make_aware(datetime.combine(new_day, time(10))) - timedelta(days=1)


@pytest.mark.django_db
def test_cancellation_cancels_pending_job():
    doctor = User.objects.create_user(username='cancel-doctor', role='CLINICIAN')
    patient = Patient.objects.create(user=User.objects.create_user(username='cancel-patient', role='PATIENT'))
    appointment = Appointment.objects.create(patient=patient, clinician=doctor, appointment_date=timezone.localdate(), appointment_time=time(9))
    job = ReminderJob.objects.create(appointment=appointment, due_at=timezone.now())
    client = APIClient()
    client.force_authenticate(doctor)
    url = reverse('appointment-status-update', kwargs={'appointment_id': appointment.appointment_id})
    assert client.patch(url, {'status': 'CANCELLED'}, format='json').status_code == 200
    job.refresh_from_db()
    assert job.state == 'CANCELLED'


@pytest.mark.django_db
def test_backfill_adds_future_scheduled_jobs_idempotently():
    doctor = User.objects.create_user(username='backfill-doctor', role='CLINICIAN')
    patient = Patient.objects.create(user=User.objects.create_user(username='backfill-patient', role='PATIENT'))
    appointment = Appointment.objects.create(patient=patient, clinician=doctor,
        appointment_date=timezone.localdate() + timedelta(days=3), appointment_time=time(9))
    backfill = import_module('notifications.migrations.0002_backfill_reminders').backfill_reminders
    editor = SimpleNamespace(connection=connection)
    backfill(apps, editor)
    backfill(apps, editor)
    assert ReminderJob.objects.filter(appointment=appointment).count() == 1
