from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AmenitiesConfig(AppConfig):
    name = 'django_amenities'
    verbose_name = _("Amenities App")
