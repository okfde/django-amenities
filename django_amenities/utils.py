import re
from itertools import islice
from datetime import datetime

from django.contrib.gis.geos import Point

import pytz
from lxml import etree

from .models import Amenity

BASIC_TAGS = (
    'name', 'addr:country', 'addr:street', 'addr:housenumber',
    'addr:postcode', 'addr:city',
)

NUM_START = re.compile(r'^\d+')


def get_amenities(filename, version=0, osm_ids=None, topics=None,
                  category_func=None, start=0,):
    with open(filename, 'rb') as f:
        context = etree.iterparse(f, events=("start",), tag='node')
        for action, elem in islice(context, start, None):

            if osm_ids is not None:
                if int(elem.attrib['id']) not in osm_ids:
                    continue

            basic = get_data_for_node(
                elem, version=version, topics=topics,
                category_func=category_func
            )
            if basic is None:
                continue
            yield basic


def get_osm_id_set(filename, timestamp=None):
    return set(get_osm_ids(filename, timestamp=timestamp))


def get_osm_ids(filename, timestamp=None):
    with open(filename, 'rb') as f:
        context = etree.iterparse(f, events=("start",), tag='node')
        for action, elem in context:
            if timestamp is not None:
                last_update = datetime.strptime(
                    elem.attrib['timestamp'], "%Y-%m-%dT%H:%M:%SZ"
                )
                if last_update < timestamp:
                    continue
            yield int(elem.attrib['id'])


def get_topics(basic, topics):
    return [
        topic
        for topic, tags in topics.items()
        if node_has_tags(basic, tags)
    ]


def node_has_tags(basic, tags):
    for k, v in tags:
        if k in basic:
            if basic[k] == v or v == "*":
                return True
    return False


def get_data_for_node(elem, version=0, topics=None, category_func=None):
    data = {
        x.attrib['k']: x.attrib['v']
        for x in elem.xpath('./tag')
    }

    attrs = elem.attrib
    last_update = datetime.strptime(
        attrs['timestamp'], "%Y-%m-%dT%H:%M:%SZ"
    )
    last_update = pytz.utc.localize(last_update, is_dst=None)
    basic = {
        k.replace('addr:', ''): v for k, v in data.items()
        if k in BASIC_TAGS
    }

    if category_func:
        basic['category'] = category_func(data)
    if topics:
        basic['topics'] = get_topics(data, topics)

    if 'housenumber' in basic:
        if (basic['housenumber'] and
                not NUM_START.search(basic['housenumber'])):
            basic['housenumber'] = ''
        else:
            basic['housenumber'] = basic['housenumber'][:10]
    if 'country' in basic:
        basic['country'] = basic['country'][:2]
    tags = {k: v for k, v in data.items() if k not in BASIC_TAGS}
    basic.update(dict(
        osm_id=int(attrs['id']),
        geo=Point(float(attrs['lon']), float(attrs['lat'])),
        last_update=last_update,
        version=version,
        tags=tags,
    ))
    return basic


def create_amenities_bulk(objs, batch_size=1000):
    i = -1
    while True:
        i += 1
        batch = list(islice(objs, batch_size))
        if not batch:
            break
        Amenity.objects.bulk_create([
            Amenity(**b) for b in batch
        ], batch_size)
        yield i


def update_amenities_bulk(objs, batch_size=1000):
    for i, obj in enumerate(objs):
        Amenity.objects.filter(osm_id=obj['osm_id']).update(
            **obj
        )
        if i % batch_size == 0:
            yield i
