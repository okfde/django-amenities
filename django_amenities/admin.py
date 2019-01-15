from django.contrib import admin

from .models import Amenity


class AmenityAdmin(admin.ModelAdmin):
    date_hierarchy = 'last_update'
    search_fields = ('name', 'city', 'postcode')
    list_display = ('name', 'street', 'housenumber', 'postcode', 'city',)


admin.site.register(Amenity, AmenityAdmin)
