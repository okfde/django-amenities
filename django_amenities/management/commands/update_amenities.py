import argparse
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import translation

from ...updater import AmenityUpdater


class AmenityCommandUpdater(AmenityUpdater):
    def __init__(self, *args, **kwargs):
        self.stdout = kwargs.pop('stdout')
        super().__init__(*args, **kwargs)

    def progress(self, update):
        self.stdout.write(update)


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


class Command(BaseCommand):
    help = "Update amenities"
    updater_class = AmenityCommandUpdater

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)
        parser.add_argument('timestamp', type=valid_date)
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete obsolete',
        )

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)

        self.stdout.write(
            'Starting update with {filename} on date {timestamp}'.format(
                **options
            )
        )

        updater = self.updater_class(
            options['filename'], timestamp=options['timestamp'],
            topics=settings.AMENITY_TOPICS,
            stdout=self.stdout,
            delete_obsolete=options['delete'],
            category_func=getattr(settings, 'AMENITY_CATEGORY_FUNC', None)
        )
        updater.run()
