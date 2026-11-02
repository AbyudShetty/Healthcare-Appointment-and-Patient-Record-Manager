import hashlib
import hmac
import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from audit_logs.models import AuditLog


class Command(BaseCommand):
    help = 'Export audit events as signed JSON lines. Store the output in independently controlled immutable storage.'

    def handle(self, *args, **options):
        key = os.environ.get('AUDIT_EXPORT_HMAC_KEY', '')
        if len(key.encode()) < 32:
            raise CommandError('AUDIT_EXPORT_HMAC_KEY must contain at least 32 bytes.')
        mac = hmac.new(key.encode(), digestmod=hashlib.sha256)
        count = 0
        cutoff = timezone.now()
        for row in AuditLog.objects.filter(timestamp__lte=cutoff).order_by('id').values(
                'id', 'user_id', 'action', 'details', 'ip_address', 'timestamp').iterator():
            row['timestamp'] = row['timestamp'].isoformat()
            line = json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
            mac.update((line + '\n').encode())
            self.stdout.write(line)
            count += 1
        manifest = {'count': count, 'cutoff': cutoff.isoformat()}
        manifest_line = json.dumps(manifest, sort_keys=True, separators=(',', ':'))
        mac.update((manifest_line + '\n').encode())
        manifest['hmac_sha256'] = mac.hexdigest()
        self.stdout.write(json.dumps({'manifest': manifest}, sort_keys=True, separators=(',', ':')))
