import re
from itertools import islice
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation
from django.contrib.gis.geos import Point

import pytz
from lxml import etree

from ...models import Amenity

NUM_START = re.compile('^\d+')


class Command(BaseCommand):
    help = "Switch venue requests"

    def add_arguments(self, parser):
        parser.add_argument('command', type=str)
        parser.add_argument('filename', type=str)
        parser.add_argument('skip', type=int, default=0, nargs='?')

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)

        self.stdout.write('Starting {command} of {filename} at {skip}'.format(
            **options
        ))
        command = options['command']
        batch_size = 1000
        skip = options['skip'] * batch_size

        if command == 'insert':
            objs = self.get_amenities(
                options['filename'], as_objects=True, start=skip
            )
            i = -1
            while True:
                i += 1
                self.stdout.write(str(i), ending='\r')
                batch = list(islice(objs, batch_size))
                if not batch:
                    break
                Amenity.objects.bulk_create(batch, batch_size)
        elif command == 'update':
            objs = self.get_amenities(
                options['filename'], as_objects=False, start=skip
            )
            for i, amenity in enumerate(objs):
                if i % 1000 == 0:
                    self.stdout.write(str(i), ending='\r')
                Amenity.objects.get_or_create(
                    osm_id=amenity['osm_id'],
                    defaults=amenity
                )
        self.stdout.write('\nDone')

    def get_amenities(self, filename, version=0, start=0, as_objects=False):
        basic_tags = (
            'name', 'addr:country', 'addr:street', 'addr:housenumber',
            'addr:postcode', 'addr:city', 'amenity', 'shop'
        )
        with open(filename, 'rb') as f:
            context = etree.iterparse(f, events=("start",), tag='node')
            for action, elem in islice(context, start, None):
                data = {
                    x.attrib['k']: x.attrib['v']
                    for x in elem.xpath('./tag')
                }
                if 'amenity' not in data and 'shop' not in data:
                    continue

                attrs = elem.attrib
                last_update = datetime.strptime(
                    attrs['timestamp'], "%Y-%m-%dT%H:%M:%SZ"
                )
                last_update = pytz.utc.localize(last_update, is_dst=None)
                basic = {k.replace('addr:', ''): v for k, v in data.items()
                         if k in basic_tags}
                if 'shop' in basic:
                    basic['amenity'] = basic.pop('shop')
                if 'housenumber' in basic:
                    if (basic['housenumber'] and
                            not NUM_START.search(basic['housenumber'])):
                        basic['housenumber'] = ''
                    else:
                        basic['housenumber'] = basic['housenumber'][:10]
                if 'country' in basic:
                    basic['country'] = basic['country'][:2]
                tags = {k: v for k, v in data.items() if k not in basic_tags}
                basic.update(dict(
                    osm_id=int(attrs['id']),
                    geo=Point(float(attrs['lon']), float(attrs['lat'])),
                    last_update=last_update,
                    version=version,
                    tags=tags,
                ))
                if as_objects:
                    yield Amenity(**basic)
                else:
                    yield basic
