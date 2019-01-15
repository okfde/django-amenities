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
        parser.add_argument('filename', type=str)
        parser.add_argument('skip', type=int, default=0, nargs='?')

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)

        Amenity.objects.all().delete()
        self.stdout.write('Starting import of {filename} at {skip}'.format(
            **options
        ))
        batch_size = 1000
        skip = options['skip'] * batch_size
        objs = self.get_amenities(options['filename'], start=skip)

        i = -1
        while True:
            i += 1
            self.stdout.write(str(i), ending='\r')
            batch = list(islice(objs, batch_size))
            if not batch:
                break
            Amenity.objects.bulk_create(batch, batch_size)
        self.stdout.write('\nDone')

    def get_amenities(self, filename, version=0, start=0):
        basic_tags = (
            'name', 'addr:country', 'addr:street', 'addr:housenumber',
            'addr:postcode', 'addr:city', 'amenity', 'shop'
        )
        with open(filename, 'rb') as f:
            context = etree.iterparse(f, events=("start",), tag='node')
            for action, elem in islice(context, start, None):
                attrs = elem.attrib
                last_update = datetime.strptime(
                    attrs['timestamp'], "%Y-%m-%dT%H:%M:%SZ"
                )
                last_update = pytz.utc.localize(last_update, is_dst=None)
                data = {
                    x.attrib['k']: x.attrib['v']
                    for x in elem.xpath('./tag')
                }
                basic = {k.replace('addr:', ''): v for k, v in data.items() if k in basic_tags}
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
                yield Amenity(
                   osm_id=int(attrs['id']),
                   geo=Point(float(attrs['lon']), float(attrs['lat'])),
                   last_update=last_update,
                   version=version,
                   tags=tags,
                   **basic
                )
