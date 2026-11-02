import pytest
import hashlib
import hmac
import io
import json
from unittest.mock import patch
from django.core.management import call_command, CommandError
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


@pytest.mark.django_db
def test_signed_audit_export_detects_changes(tmp_path):
    log_action(action='TEST_EVENT', details='test')
    key = 'test-key-' * 5
    output = io.StringIO()
    with patch.dict('os.environ', {'AUDIT_EXPORT_HMAC_KEY': key}):
        call_command('export_audit', stdout=output)
    lines = output.getvalue().splitlines()
    manifest = json.loads(lines[-1])['manifest']
    signature = manifest.pop('hmac_sha256')
    payload = ''.join(line + '\n' for line in lines[:-1]) + json.dumps(manifest, sort_keys=True, separators=(',', ':')) + '\n'
    assert hmac.compare_digest(signature, hmac.new(key.encode(), payload.encode(), hashlib.sha256).hexdigest())
    assert manifest['count'] == 1
    path = tmp_path / 'audit.jsonl'
    path.write_text(output.getvalue(), encoding='utf-8')
    with patch.dict('os.environ', {'AUDIT_EXPORT_HMAC_KEY': key}):
        call_command('verify_audit_export', str(path), stdout=io.StringIO())
        path.write_text(output.getvalue().replace('TEST_EVENT', 'OTHER_EVENT'), encoding='utf-8')
        with pytest.raises(CommandError):
            call_command('verify_audit_export', str(path), stdout=io.StringIO())


@pytest.mark.django_db
def test_failed_login_and_denied_record_access_are_audited_without_password():
    patient = User.objects.create_user(username='audit-owner', password='Password123!', role='PATIENT')
    outsider = User.objects.create_user(username='audit-outsider', password='Password123!', role='PATIENT')
    profile = Patient.objects.create(user=patient)
    client = APIClient()
    assert client.post(reverse('token_obtain_pair'), {'username': patient.username, 'password': 'wrong-secret'}, format='json').status_code == 401
    event = AuditLog.objects.get(action='LOGIN_FAILED')
    assert 'wrong-secret' not in event.details
    client.force_authenticate(outsider)
    assert client.get(reverse('secure-history', kwargs={'patient_id': profile.patient_id})).status_code == 403
    assert AuditLog.objects.filter(user=outsider, action='RECORD_HISTORY_DENIED').exists()
