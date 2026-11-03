from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from authentication.models import MFADevice, User
from audit_logs.utils import log_action


class Command(BaseCommand):
    help = 'Reset MFA after an administrator has independently verified the account holder.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--operator', required=True, help='Username of the administrator authorizing the reset.')
        parser.add_argument('--reason', required=True, help='Non-sensitive ticket or case reference.')
        parser.add_argument('--identity-verified', action='store_true')

    def handle(self, *args, **options):
        if not options['identity_verified']:
            raise CommandError('Identity verification must be completed before an MFA reset.')
        with transaction.atomic():
            operator = User.objects.filter(username=options['operator'], role='ADMIN', is_active=True).first()
            target = User.objects.select_for_update().filter(username=options['username']).first()
            if not operator or not target:
                raise CommandError('Active administrator or target account not found.')
            target.mfa_enabled = False
            target.auth_version += 1
            target.save(update_fields=['mfa_enabled', 'auth_version'])
            MFADevice.objects.filter(user=target).delete()
            log_action(user=operator, action='MFA_ADMIN_RESET',
                       details=f"Account {target.pk}; case {options['reason'][:100]}")
        self.stdout.write('MFA reset. All prior API sessions were revoked.')
