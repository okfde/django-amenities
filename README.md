# Django Amenities

A Django app that stores OSM amenities,
" shops and tourism nodes for=querying".


## Django settings

```python

AMENITY_CATEGORY_FUNC = None

AMENITY_TOPICS = {
    "public": (
      ("building", "civic"),
      ("building", "school"),
      ("building", "government"),
      ("amenity", "townhall"),
      ("amenity", "library"),
      ("amenity", "police"),
      ("amenity", "school"),
      ("amenity", "community_centre"),
      ("amenity", "archive"),
      ("amenity", "courthouse"),
      ("amenity", "hospital"),
      ("amenity", "public_building"),
      ("office", "government"),
      ("office", "administrative"),
      ("government", "*"),
    ),
}

```