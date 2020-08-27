from django.db.models import Max

from . import registry
from .models import Amenity
from .utils import (
    get_osm_id_set, get_amenities, create_amenities_bulk,
    update_amenities_bulk, get_topics
)


def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))


CATEGORY_KEYS = ['amenity', 'shop', 'tourism', 'government']


def basic_category_func(basic):
    for cat in CATEGORY_KEYS:
        if cat in basic:
            return basic[cat]
    return ''


class AmenityUpdater:
    def __init__(self, filename, timestamp=None, topics=None,
                 category_func=None, delete_obsolete=False):
        self.filename = filename
        self.timestamp = timestamp
        self.topics = topics
        self.delete_obsolete = delete_obsolete
        self.category_func = category_func or basic_category_func

    def progress(self, update):
        print(update)

    def run(self):
        self.update_osm_ids()

    def apply_topics(self):
        for amenity in Amenity.objects.iterator():
            topics = get_topics(amenity.tags, self.topics)
            if set(topics) != set(amenity.topics):
                Amenity.objects.filter(id=amenity.id).update(
                    topics=topics
                )

    def get_used_osm_ids(self):
        result = set()
        for user_result in registry.iter_users('get_used_osm_ids'):
            result |= user_result
        return result

    def get_safe_update_osm_ids(self, used_existing_osm_ids):
        result = set()
        gen = registry.iter_users(
            'get_safe_update_osm_ids', used_existing_osm_ids
        )
        for user_result in gen:
            result |= user_result
        return result

    def update_osm_ids(self):
        base_qs = Amenity.objects.all()
        next_version = (
            Amenity.objects.all().aggregate(
                max_version=Max('version')
            )['max_version'] or 0
        ) + 1

        existing_osm_ids = set(
            base_qs.values_list('osm_id', flat=True)
        )
        existing_outdated_osm_ids = set(
            base_qs.filter(
                version__lt=next_version
            ).values_list('osm_id', flat=True)
        )
        current_osm_ids = get_osm_id_set(
            self.filename
        )
        current_updated_osm_ids = get_osm_id_set(
            self.filename, timestamp=self.timestamp
        )

        obsolete_osm_ids = existing_osm_ids - current_osm_ids

        used_osm_ids = self.get_used_osm_ids()

        if self.delete_obsolete:
            remove_osm_ids = list(obsolete_osm_ids - used_osm_ids)

            self.progress('Removing {} obsolete amenities'.format(
                len(remove_osm_ids))
            )

            for chunk in chunks(remove_osm_ids, 100):
                Amenity.objects.filter(osm_id__in=chunk).delete()

        # Create these amenities
        fresh_osm_ids = current_osm_ids - existing_osm_ids

        self.progress('Creating {} new amenities'.format(
            len(fresh_osm_ids))
        )
        fresh_amenities = get_amenities(
            self.filename, version=next_version,
            topics=self.topics,
            category_func=self.category_func,
            osm_ids=fresh_osm_ids
        )
        for progress in create_amenities_bulk(fresh_amenities):
            self.progress('Batch-progress %s' % progress)

        # Update these amenities
        update_osm_ids = current_updated_osm_ids & existing_outdated_osm_ids
        direct_update_osm_ids = update_osm_ids - used_osm_ids

        self.progress('Updating existing unused {} amenities'.format(
            len(direct_update_osm_ids))
        )
        updated_amenities = get_amenities(
            self.filename, version=next_version,
            topics=self.topics,
            category_func=self.category_func,
            osm_ids=direct_update_osm_ids
        )
        for progress in update_amenities_bulk(updated_amenities):
            self.progress('Batch-progress %s' % progress)

        used_existing_osm_ids = update_osm_ids & used_osm_ids

        self.progress('Checking existing used {} amenities'.format(
            len(used_existing_osm_ids))
        )

        safe_update_osm_ids = self.get_safe_update_osm_ids(
            used_existing_osm_ids
        )

        self.progress('Update existing used safe {} amenities'.format(
            len(used_existing_osm_ids))
        )

        safe_updated_amenities = get_amenities(
            self.filename, version=next_version,
            topics=self.topics, category_func=self.category_func,
            osm_ids=safe_update_osm_ids
        )
        for progress in update_amenities_bulk(safe_updated_amenities):
            self.progress('Batch-progress %s' % progress)
