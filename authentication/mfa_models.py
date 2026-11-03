from django.conf import settings
from django.db import models


class MFADevice(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mfa_device')
    secret_encrypted = models.TextField()
    pending_expires_at = models.DateTimeField(null=True, blank=True)
    last_counter = models.BigIntegerField(default=-1)
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    recovery_hashes = models.JSONField(default=list)
