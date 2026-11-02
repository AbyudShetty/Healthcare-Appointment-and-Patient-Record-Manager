import hashlib
import hmac
import json
import os

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Verify an audit export created by export_audit.'

    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, *args, **options):
        key = os.environ.get('AUDIT_EXPORT_HMAC_KEY', '')
        if len(key.encode()) < 32:
            raise CommandError('AUDIT_EXPORT_HMAC_KEY must contain at least 32 bytes.')
        mac = hmac.new(key.encode(), digestmod=hashlib.sha256)
        count = 0
        try:
            with open(options['path'], encoding='utf-8') as source:
                previous = None
                for line in source:
                    if previous is not None:
                        json.loads(previous)
                        mac.update(previous.encode())
                        count += 1
                    previous = line
                if previous is None:
                    raise ValueError('Empty export')
                manifest = json.loads(previous)['manifest']
                signature = manifest.pop('hmac_sha256')
                mac.update((json.dumps(manifest, sort_keys=True, separators=(',', ':')) + '\n').encode())
                if manifest['count'] != count or not hmac.compare_digest(signature, mac.hexdigest()):
                    raise ValueError('Signature or count does not match')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CommandError('Audit export verification failed.') from exc
        self.stdout.write(f'Valid audit export: {count} entries; cutoff {manifest["cutoff"]}.')
