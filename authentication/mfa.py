import secrets
from datetime import timedelta

import pyotp
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from authentication.models import MFADevice, User
from electronic_records.encryption import decrypt


def generate_recovery_codes():
    codes = [secrets.token_hex(5) for _ in range(10)]
    return codes, [make_password(code) for code in codes]


def consume_code(user_id, code, *, enrollment=False):
    """Atomically validate a TOTP or one-use recovery code, including lockout."""
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)
        device = MFADevice.objects.select_for_update().filter(user=user).first()
        now = timezone.now()
        if not device or (device.locked_until and device.locked_until > now):
            return False, []
        if enrollment and (user.mfa_enabled or not device.pending_expires_at or device.pending_expires_at <= now):
            return False, []
        if not enrollment and not user.mfa_enabled:
            return False, []

        matched = False
        current = int(now.timestamp()) // 30
        totp = pyotp.TOTP(decrypt(device.secret_encrypted))
        for counter in range(current - 1, current + 2):
            if counter > device.last_counter and secrets.compare_digest(totp.at(counter * 30), str(code)):
                device.last_counter = counter
                matched = True
                break
        if not matched and not enrollment:
            for index, encoded in enumerate(device.recovery_hashes):
                if check_password(str(code), encoded):
                    device.recovery_hashes.pop(index)
                    matched = True
                    break
        if not matched:
            device.failed_attempts += 1
            if device.failed_attempts >= 5:
                device.locked_until = now + timedelta(minutes=15)
                device.failed_attempts = 0
            device.save()
            return False, []

        device.failed_attempts = 0
        device.locked_until = None
        recovery_codes = []
        if enrollment:
            recovery_codes, device.recovery_hashes = generate_recovery_codes()
            device.pending_expires_at = None
            user.mfa_enabled = True
            user.auth_version += 1
            user.save(update_fields=['mfa_enabled', 'auth_version'])
        device.save()
        return True, recovery_codes
