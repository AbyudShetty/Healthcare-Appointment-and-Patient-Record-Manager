import logging
from datetime import timedelta
from uuid import uuid4

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from notifications.models import ReminderJob
from notifications.tasks import schedule_appointment_reminder

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 5
LEASE = timedelta(minutes=5)


def process_one_reminder():
    now = timezone.now()
    with transaction.atomic():
        job = (ReminderJob.objects.select_for_update(skip_locked=True)
               .filter(Q(state='PENDING', due_at__lte=now) | Q(state='RUNNING', locked_until__lt=now))
               .order_by('due_at', 'pk').first())
        if not job:
            return False
        if job.attempts >= MAX_ATTEMPTS:
            job.state = 'FAILED'
            job.last_error = 'Delivery attempt limit reached'
            job.updated_at = now
            job.save(update_fields=['state', 'last_error', 'updated_at'])
            return True
        if job.appointment.status != 'SCHEDULED':
            job.state = 'CANCELLED'
            job.updated_at = now
            job.save(update_fields=['state', 'updated_at'])
            return True
        job.state = 'RUNNING'
        job.claim_token = uuid4().hex
        job.locked_until = now + LEASE
        job.attempts += 1
        job.updated_at = now
        job.save(update_fields=['state', 'claim_token', 'locked_until', 'attempts', 'updated_at'])
        job_id, token, appointment_id, attempts = job.pk, job.claim_token, job.appointment_id, job.attempts

    try:
        result = schedule_appointment_reminder(appointment_id)
    except Exception:
        logger.warning('Reminder delivery failed for job %s', job_id)
        now = timezone.now()
        ReminderJob.objects.filter(pk=job_id, state='RUNNING', claim_token=token).update(
            state='FAILED' if attempts >= MAX_ATTEMPTS else 'PENDING',
            due_at=now + timedelta(minutes=min(2 ** attempts, 60)),
            locked_until=None, claim_token='', last_error='Email delivery failed', updated_at=now,
        )
    else:
        now = timezone.now()
        ReminderJob.objects.filter(pk=job_id, state='RUNNING', claim_token=token).update(
            state='SENT' if result.startswith('Reminder sent') else 'CANCELLED',
            sent_at=now if result.startswith('Reminder sent') else None,
            locked_until=None, claim_token='', last_error='', updated_at=now,
        )
    return True
