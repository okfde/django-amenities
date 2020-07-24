from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import ArrayField, JSONField


class Amenity(models.Model):
    osm_id = models.BigIntegerField()
    name = models.CharField(max_length=1000)
    last_update = models.DateTimeField(null=True, blank=True)

    geo = models.PointField(
        null=True, blank=True,
        geography=True, spatial_index=True
    )
    topics = ArrayField(
        models.CharField(max_length=200),
        default=list, blank=True
    )

    country = models.CharField(max_length=2, blank=False)
    street = models.CharField(max_length=255, blank=True)
    housenumber = models.CharField(max_length=10, blank=True)
    postcode = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=255, blank=True)
    amenity = models.CharField(max_length=255, blank=True)
    version = models.IntegerField(default=0)

    tags = JSONField(blank=True, default=dict)

    class Meta:
        verbose_name = _('amenity')
        verbose_name_plural = _('amenities')

    def __str__(self):
        return self.name

    @property
    def ident(self):
        return '{}_{}'.format(self.id, self.osm_id)

    @property
    def address(self):
        return '\n'.join(x for x in (
            '{} {}'.format(
                self.street,
                self.housenumber
            ).strip(),
            '{} {}'.format(
                self.postcode,
                self.city
            ).strip()
        ) if x)
