from django.contrib import admin

from .models import Amenity


class TopicArrayFieldListFilter(admin.SimpleListFilter):
    """This is a list filter based on the values
    from a model's `topics` ArrayField. """

    title = 'Topics'
    parameter_name = 'topics'

    def lookups(self, request, model_admin):
        # Very similar to our code above, but this method must return a
        # list of tuples: (lookup_value, human-readable value). These
        # appear in the admin's right sidebar

        topics = Amenity.objects.values_list("topics", flat=True)
        topics = [(t, t) for sublist in topics for t in sublist if t]
        topics = sorted(set(topics))
        return topics

    def queryset(self, request, queryset):
        # when a user clicks on a filter, this method gets called. The
        # provided queryset with be a queryset of Items, so we need to
        # filter that based on the clicked keyword.

        lookup_value = self.value()  # The clicked keyword. It can be None!
        if lookup_value:
            # the __contains lookup expects a list, so...
            queryset = queryset.filter(topics__contains=[lookup_value])
        return queryset


class AmenityAdmin(admin.ModelAdmin):
    date_hierarchy = 'last_update'
    search_fields = ('name', 'city', 'postcode')
    list_display = (
        'name', 'street', 'housenumber', 'postcode', 'city',
        'topics'
    )
    list_filter = (TopicArrayFieldListFilter, 'version',)


admin.site.register(Amenity, AmenityAdmin)
