# Django Amenities

A Django app that stores OSM amenities, shops and tourism nodes for querying.


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

## Prepare OSM dump for import

This is how you prepare an OSM dump for import. The example includes food-related tags and public building related tags:

```bash
# Define food related tags as a comma-separated tag-list with key.value
FOOD_TAGS=amenity.bar,amenity.biergarten,amenity.cafe,amenity.fast_food,amenity.pub,amenity.restaurant,amenity.casino,amenity.cinema,amenity.nightclub,amenity.food_court,amenity.ice_cream,amenity.fuel,shop.alcohol,shop.bakery,shop.beverages,shop.butcher,shop.cheese,shop.chocolate,shop.coffee,shop.confectionery,shop.convenience,shop.deli,shop.dairy,shop.farm,shop.frozen_food,shop.greengrocer,shop.health_food,shop.ice_cream,shop.organic,shop.pasta,shop.pastry,shop.seafood,shop.spices,shop.tea,shop.wine,shop.water,shop.department_store,shop.general,shop.kiosk,shop.supermarket,shop.wholesale,tourism.hostel,tourism.hotel,tourism.theme_park

# Download latest Germany dump from GeoFabrik (thanks GeoFabrik!)
wget -N https://download.geofabrik.de/europe/germany-latest.osm.pbf

# Convert OSM dump to nodes only with osmconvert. All non-nodes (areas, relationships) are converted to centroid node and get a new ID with big offset
osmconvert germany-latest.osm.pbf --all-to-nodes -o=germany_nodes.pbf --max-objects=1000000000

DATA_FILE=germany_nodes.pbf

# Osmosis reads the new nodes-based data file and extracts the tags
# Wildcard tags need to be extracted separately and can be combined like this

osmosis \
--read-pbf "$DATA_FILE" \
--log-progress \
--node-key-value keyValueList="${FOOD_TAGS}" \
--sort \
--read-pbf "$DATA_FILE" \
--log-progress \
--node-key-value keyValueList="building.public,building.civic,building.school,building.government,amenity.townhall,amenity.library,amenity.police,amenity.school,amenity.community_centre,amenity.archive,amenity.courthouse,amenity=hospital,amenity.public_building,office.government,office.administrative" \
--sort \
--read-pbf "$DATA_FILE" \
--tf accept-nodes 'government=*' \
--sort \
--merge --merge \
--write-xml amenities.xml

# The resulting XML file can be loaded with the update_amenities command
# It takes a date which represents the last load date. Nodes updated after this date are also updated in the database if present.

python manage.py update_amenities amenities.xml 2020-07-16

```

`update_amenities` works by:
1. Getting the next higher version number (by looking at the highest existing one)
2. Getting a list of existing OSM ids in the database
3. Getting a list of OSM ids from the update file
4. Getting a list of OSM ids from the update file that are updated after the given date
5. Finding OSM ids that are present in the database but no longer present in the update (obsolete IDs)
6. Detecting IDs of Amenity objects that have been used (e.g. referenced) by other apps (other apps indicate this by registering with the amenities registry and providing callbacks)
7. All unused and obsolete Amenity objects are removed if the `--delete` flag is given
8. Created all new OSM IDs that do not exist yet in the database
9. Update existing OSM IDs that are outdated and not used
10. Update OSM IDs that are used and need update and can be safely updated ('safely' is determined by other apps through registry callback)

### OSM ID update safety

OSM IDs behave like database primary keys and not like WikiData Item IDs. That means that they uniquely reference an object, but this object can be changed to represent something else (e.g. a fast food shop with an OSM ID can close and be replaced with a restaurant and have the same OSM ID). This can be good (it's a new venue in the same place), but also bad (it's not the same venue). Django apps using the OSM data can try to determine if an update is safe to apply by looking at the tags and detecting if it's still the same kind of object.
