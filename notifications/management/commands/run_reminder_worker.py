import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from notifications.worker import process_one_reminder


class Command(BaseCommand):
    help = 'Poll and deliver durable appointment reminder jobs.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true', help='Process at most one job and exit.')
        parser.add_argument('--poll-seconds', type=float, default=5)

    def handle(self, *args, **options):
        while True:
            close_old_connections()
            processed = process_one_reminder()
            if options['once']:
                break
            if not processed:
                time.sleep(max(options['poll_seconds'], 0.1))
