import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from audit_logs.models import AuditLog
from audit_logs.utils import log_action
from authentication.models import User
from patients.models import Patient


@pytest.mark.django_db
def test_audit_persists_and_only_admin_can_list():
    patient_user = User.objects.create_user(username='audit-patient', role='PATIENT')
    admin = User.objects.create_user(username='audit-admin', role='ADMIN')
    patient = Patient.objects.create(user=patient_user)
    client = APIClient()
    client.force_authenticate(patient_user)
    assert client.get(reverse('secure-history', kwargs={'patient_id': patient.patient_id})).status_code == 200
    assert AuditLog.objects.filter(user=patient_user, action='RECORD_HISTORY_VIEWED').exists()
    assert client.get(reverse('admin-logs-list')).status_code == 403
    log_action(user=admin, action='TEST_EVENT', details='test')
    client.force_authenticate(admin)
    result = client.get(reverse('admin-logs-list'))
    assert result.status_code == 200
    assert any(item['action'] == 'TEST_EVENT' for item in result.data['results'])
