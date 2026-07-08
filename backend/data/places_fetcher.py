"""
Moka Fit Score — Google Places API Data Fetcher

Fetches real merchant data from Google Places API (New) for Istanbul.
Searches for businesses in target categories across key Istanbul districts,
then maps results to our Merchant schema.

Usage:
    python -m data.places_fetcher                   # Fetch all categories
    python -m data.places_fetcher --category cafe   # Single category
    python -m data.places_fetcher --max-per-query 20 # Limit per search

Requires:
    GOOGLE_PLACES_API_KEY in .env
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path

# Ensure backend/ is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
PLACE_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"

# Map our internal categories to Google Places included types
CATEGORY_TYPE_MAP = {
    "restaurant": ["restaurant", "turkish_restaurant", "kebab_shop", "seafood_restaurant"],
    "cafe": ["cafe", "coffee_shop", "bakery"],
    "clothing_store": ["clothing_store", "boutique", "shoe_store"],
    "electronics_store": ["electronics_store", "computer_store", "mobile_phone_store"],
    "beauty_salon": ["beauty_salon", "hair_salon", "barber_shop", "spa"],
}

# Key Istanbul districts with center coordinates
ISTANBUL_DISTRICTS = {
    "Beyoğlu":    (41.0370, 28.9770),
    "Kadıköy":    (40.9819, 29.0290),
    "Beşiktaş":   (41.0430, 29.0070),
    "Şişli":      (41.0602, 28.9877),
    "Bakırköy":   (40.9800, 28.8770),
    "Üsküdar":    (41.0234, 29.0153),
    "Fatih":      (41.0186, 28.9397),
    "Sarıyer":    (41.1670, 29.0570),
    "Maltepe":    (40.9345, 29.1300),
    "Ataşehir":   (40.9923, 29.1244),
    "Kartal":     (40.8897, 29.1857),
    "Pendik":     (40.8755, 29.2520),
}

# Fields to request from the API (controls billing)
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.userRatingCount",
    "places.priceLevel",
    "places.websiteUri",
    "places.nationalPhoneNumber",
    "places.internationalPhoneNumber",
    "places.primaryType",
    "places.reviews",
    "places.types",
])

# Mapping from Google price level enum to numeric
PRICE_LEVEL_MAP = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}


# ---------------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------------

def _search_nearby(
    lat: float,
    lng: float,
    included_types: list[str],
    radius_m: float = 3000.0,
    max_results: int = 20,
    api_key: str = "",
) -> list[dict]:
    """
    Search for places near a point using the Places API (New).

    Args:
        lat, lng: Center coordinates.
        included_types: Google Places types to search for.
        radius_m: Search radius in meters.
        max_results: Maximum results to return (max 20 per API).
        api_key: Google API key.

    Returns:
        List of raw place dicts from the API.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    body = {
        "includedTypes": included_types,
        "maxResultCount": min(max_results, 20),
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m,
            }
        },
        "languageCode": "tr",
    }

    try:
        resp = requests.post(PLACES_NEARBY_URL, json=body, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("places", [])
    except requests.exceptions.HTTPError as e:
        print(f"  [WARN] API error for ({lat:.4f}, {lng:.4f}): {e}")
        if resp.status_code == 429:
            print("  [WARN] Rate limited, waiting 5s...")
            time.sleep(5)
        return []
    except Exception as e:
        print(f"  [ERROR] Request failed: {e}")
        return []


def _extract_reviews_text(place: dict) -> str:
    """Extract review texts from a place result."""
    reviews = place.get("reviews", [])
    texts = []
    for review in reviews[:10]:  # Limit to 10 reviews
        original = review.get("originalText", {})
        text = original.get("text", "")
        if text:
            texts.append(text)
    return " | ".join(texts) if texts else ""


def _detect_district(address: str) -> str | None:
    """Try to detect the Istanbul district from the formatted address."""
    if not address:
        return None
    for district in ISTANBUL_DISTRICTS:
        if district.lower() in address.lower():
            return district
    # Common ASCII alternatives
    ascii_map = {
        "Beyoglu": "Beyoğlu",
        "Kadikoy": "Kadıköy",
        "Besiktas": "Beşiktaş",
        "Sisli": "Şişli",
        "Bakirkoy": "Bakırköy",
        "Uskudar": "Üsküdar",
        "Sariyer": "Sarıyer",
        "Atasehir": "Ataşehir",
    }
    for ascii_name, turkish_name in ascii_map.items():
        if ascii_name.lower() in address.lower():
            return turkish_name
    return None


def _map_to_merchant(place: dict, our_category: str) -> dict:
    """
    Map a Google Places API result to our Merchant schema.

    Args:
        place: Raw place dict from the API.
        our_category: Our internal category label.

    Returns:
        Dict matching the Merchant model fields.
    """
    location = place.get("location", {})
    display_name = place.get("displayName", {})
    address = place.get("formattedAddress", "")

    price_str = place.get("priceLevel", "")
    price_level = PRICE_LEVEL_MAP.get(price_str, None)

    return {
        "place_id": place.get("id", ""),
        "name": display_name.get("text", "Unknown"),
        "category": our_category,
        "latitude": location.get("latitude", 0.0),
        "longitude": location.get("longitude", 0.0),
        "address": address,
        "district": _detect_district(address),
        "rating": place.get("rating", None),
        "review_count": place.get("userRatingCount", 0),
        "price_level": price_level,
        "has_website": bool(place.get("websiteUri")),
        "has_phone": bool(
            place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")
        ),
        "reviews_text": _extract_reviews_text(place),
    }


# ---------------------------------------------------------------------------
# Main Fetch Logic
# ---------------------------------------------------------------------------

def fetch_real_merchants(
    categories: list[str] | None = None,
    max_per_query: int = 20,
    radius_m: float = 3000.0,
) -> list[dict]:
    """
    Fetch real merchant data from Google Places API across Istanbul districts.

    Args:
        categories: List of our category keys to fetch, or None for all.
        max_per_query: Max results per API call (max 20).
        radius_m: Search radius around each district center.

    Returns:
        List of merchant dicts ready for DB insertion.
    """
    api_key = settings.GOOGLE_PLACES_API_KEY
    if not api_key or api_key == "your_google_places_api_key_here":
        print("[ERROR] GOOGLE_PLACES_API_KEY not set in .env")
        return []

    if categories is None:
        categories = list(CATEGORY_TYPE_MAP.keys())

    all_merchants = []
    seen_ids = set()

    total_searches = len(categories) * len(ISTANBUL_DISTRICTS)
    search_num = 0

    for our_category in categories:
        google_types = CATEGORY_TYPE_MAP[our_category]
        print(f"\n{'='*60}")
        print(f"  Fetching: {our_category} ({', '.join(google_types)})")
        print(f"{'='*60}")

        for district_name, (lat, lng) in ISTANBUL_DISTRICTS.items():
            search_num += 1
            print(f"  [{search_num}/{total_searches}] {district_name}...", end=" ")

            places = _search_nearby(
                lat=lat,
                lng=lng,
                included_types=google_types,
                radius_m=radius_m,
                max_results=max_per_query,
                api_key=api_key,
            )

            new_count = 0
            for place in places:
                place_id = place.get("id", "")
                if place_id and place_id not in seen_ids:
                    seen_ids.add(place_id)
                    merchant = _map_to_merchant(place, our_category)
                    all_merchants.append(merchant)
                    new_count += 1

            print(f"found {len(places)}, {new_count} new (total: {len(all_merchants)})")

            # Respect rate limits — short delay between requests
            time.sleep(0.3)

    print(f"\n[OK] Fetched {len(all_merchants)} unique merchants total.")
    return all_merchants


def seed_database_real(
    categories: list[str] | None = None,
    max_per_query: int = 20,
    replace: bool = True,
) -> int:
    """
    Fetch real merchants from Google Places API and insert into the database.
    Then run the scoring pipeline to compute Moka Fit Scores.

    Args:
        categories: Categories to fetch, or None for all.
        max_per_query: Max results per API call.
        replace: If True, clears existing data before inserting.

    Returns:
        Number of merchants inserted and scored.
    """
    from database import SessionLocal, init_db
    from models import Merchant

    init_db()

    # Fetch from API
    merchants = fetch_real_merchants(
        categories=categories,
        max_per_query=max_per_query,
    )

    if not merchants:
        print("[ERROR] No merchants fetched.")
        return 0

    session = SessionLocal()
    try:
        if replace:
            deleted = session.query(Merchant).delete()
            session.commit()
            print(f"[INFO] Cleared {deleted} existing merchants.")

        # Insert new merchants
        db_merchants = [Merchant(**m) for m in merchants]
        session.add_all(db_merchants)
        session.commit()
        print(f"[OK] Inserted {len(db_merchants)} real merchants into the database.")

        # Print distribution
        _print_summary(merchants)

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Database insert failed: {e}")
        raise
    finally:
        session.close()

    # Run the scoring pipeline
    print("\n[INFO] Running scoring pipeline...")
    from model.scorer import score_and_update_db
    score_and_update_db()

    return len(merchants)


def _print_summary(merchants: list[dict]) -> None:
    """Print a summary of the fetched data distribution."""
    from collections import Counter

    cat_counts = Counter(m["category"] for m in merchants)
    dist_counts = Counter(m.get("district") or "Unknown" for m in merchants)
    ratings = [m["rating"] for m in merchants if m.get("rating")]
    website_count = sum(1 for m in merchants if m["has_website"])
    phone_count = sum(1 for m in merchants if m["has_phone"])
    review_texts = sum(1 for m in merchants if m.get("reviews_text"))

    print(f"\n{'='*50}")
    print(f"  Real Data Summary")
    print(f"{'='*50}")
    print(f"  Total merchants: {len(merchants)}")
    if ratings:
        print(f"  Avg rating:      {sum(ratings)/len(ratings):.1f}")
    print(f"  Has website:     {website_count} ({website_count/len(merchants)*100:.0f}%)")
    print(f"  Has phone:       {phone_count} ({phone_count/len(merchants)*100:.0f}%)")
    print(f"  Has reviews:     {review_texts} ({review_texts/len(merchants)*100:.0f}%)")
    print(f"\n  Category Distribution:")
    for cat, cnt in sorted(cat_counts.items()):
        print(f"    {cat:20s} -> {cnt}")
    print(f"\n  District Distribution:")
    for dist, cnt in sorted(dist_counts.items()):
        print(f"    {str(dist):20s} -> {cnt}")
    print(f"{'='*50}\n")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch real merchant data from Google Places API"
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=list(CATEGORY_TYPE_MAP.keys()),
        default=None,
        help="Fetch a single category (default: all)",
    )
    parser.add_argument(
        "--max-per-query",
        type=int,
        default=20,
        help="Max results per API call (default: 20, max 20)",
    )
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Don't clear existing data before inserting",
    )

    args = parser.parse_args()

    categories = [args.category] if args.category else None

    seed_database_real(
        categories=categories,
        max_per_query=args.max_per_query,
        replace=not args.no_replace,
    )
