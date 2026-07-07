"""
Moka Fit Score — Google Places API Data Collector

Collects merchant data from Google Places API for Istanbul.
Target categories: restaurant, cafe, clothing_store, electronics_store, beauty_salon

TODO: Implement in Phase 2 (currently using mock data).
"""


TARGET_CATEGORIES = [
    "restaurant",
    "cafe",
    "clothing_store",
    "electronics_store",
    "beauty_salon",
]

# Istanbul center coordinates
ISTANBUL_CENTER = {"lat": 41.0082, "lng": 28.9784}
SEARCH_RADIUS_METERS = 5000
