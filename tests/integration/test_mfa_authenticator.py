import pyotp
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient

from authentication.models import MFADevice, User
from electronic_records.encryption import encrypt


@pytest.mark.django_db
def test_user_without_mfa_can_sign_in_with_blank_optional_code():
    user = User.objects.create_user(username='no-mfa-user', password='Password123!')
    response = APIClient().post(reverse('token_obtain_pair'),
                                {'username': user.username, 'password': 'Password123!', 'mfa_code': ''}, format='json')
    assert response.status_code == 200
    assert 'access' in response.data


@pytest.mark.django_db
def test_qr_enrollment_requires_password_and_verifies_code():
    user = User.objects.create_user(username='qr-user', password='Password123!')
    client = APIClient()
    client.force_authenticate(user)
    assert client.post(reverse('mfa-enroll'), {'password': 'wrong'}, format='json').status_code == 400
    result = client.post(reverse('mfa-enroll'), {'password': 'Password123!'}, format='json')
    assert result.status_code == 200
    assert '<svg' in result.data['qr_svg']
    assert result['Cache-Control'] == 'no-store'
    secret = result.data['secret']
    assert secret not in MFADevice.objects.get(user=user).secret_encrypted
    confirmed = client.post(reverse('mfa-confirm'), {'code': pyotp.TOTP(secret).now()}, format='json')
    assert confirmed.status_code == 200
    assert len(confirmed.data['recovery_codes']) == 10


@pytest.mark.django_db
def test_authenticator_enrollment_replay_and_one_use_recovery():
    user = User.objects.create_user(username='totp-user', password='Password123!')
    client = APIClient()
    original = client.post(reverse('token_obtain_pair'), {'username': user.username, 'password': 'Password123!'}, format='json')
    assert original.status_code == 200
    secret = pyotp.random_base32()
    MFADevice.objects.create(user=user, secret_encrypted=encrypt(secret), pending_expires_at=timezone.now() + timedelta(minutes=10))
    client.force_authenticate(user)
    result = client.post(reverse('mfa-confirm'), {'code': pyotp.TOTP(secret).now()}, format='json')
    assert result.status_code == 200
    recovery = result.data['recovery_codes'][0]
    client.force_authenticate(user=None)
    replay = client.post(reverse('token_obtain_pair'), {'username': user.username, 'password': 'Password123!', 'mfa_code': pyotp.TOTP(secret).now()}, format='json')
    assert replay.status_code == 401
    login = client.post(reverse('token_obtain_pair'), {'username': user.username, 'password': 'Password123!', 'mfa_code': recovery}, format='json')
    assert login.status_code == 200
    again = client.post(reverse('token_obtain_pair'), {'username': user.username, 'password': 'Password123!', 'mfa_code': recovery}, format='json')
    assert again.status_code == 401
    refresh = client.post(reverse('token_refresh'), {'refresh': original.data['refresh']}, format='json')
    assert refresh.status_code == 401


@pytest.mark.django_db
def test_authenticator_locks_after_failures_and_pending_enrollment_expires():
    user = User.objects.create_user(username='lock-user', password='Password123!')
    secret = pyotp.random_base32()
    device = MFADevice.objects.create(user=user, secret_encrypted=encrypt(secret), pending_expires_at=timezone.now() + timedelta(minutes=10))
    client = APIClient()
    client.force_authenticate(user)
    for _ in range(5):
        assert client.post(reverse('mfa-confirm'), {'code': 'invalid'}, format='json').status_code == 400
    assert client.post(reverse('mfa-confirm'), {'code': pyotp.TOTP(secret).now()}, format='json').status_code == 400
    device.refresh_from_db()
    assert device.locked_until > timezone.now()
    device.locked_until = None
    device.pending_expires_at = timezone.now() - timedelta(seconds=1)
    device.save()
    assert client.post(reverse('mfa-confirm'), {'code': pyotp.TOTP(secret).now()}, format='json').status_code == 400
