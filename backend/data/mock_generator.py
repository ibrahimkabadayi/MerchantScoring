"""
Moka Fit Score — Mock Data Generator

Generates 250+ realistic mock merchant records across Istanbul using Faker.
Each merchant gets:
  - A category-appropriate Turkish business name
  - Real Istanbul district coordinates (with slight random offset)
  - Realistic rating, review count, price level distributions
  - Mock reviews containing cash/digital payment signals for NLP
  - Random website/phone presence

Usage:
    python -m data.mock_generator          # Generate and insert into DB
    python -m data.mock_generator --count 300  # Custom count
"""

import random
import argparse
import uuid
from datetime import datetime, timezone

from faker import Faker

fake = Faker("tr_TR")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TARGET_CATEGORIES = [
    "restaurant",
    "cafe",
    "clothing_store",
    "electronics_store",
    "beauty_salon",
]

# Real Istanbul district centers with approximate (lat, lng)
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

# Category-specific business name templates
BUSINESS_NAME_TEMPLATES = {
    "restaurant": [
        "{surname} Restaurant", "{surname} Kebap", "{surname} Lokantası",
        "{name}'nin Mutfağı", "{name} & {name} Restaurant",
        "Lezzet Durağı", "Anadolu Sofrası", "Deniz Restaurant",
        "{surname} Balık", "Chef {name}", "Gurme {surname}",
        "Tarihi {surname} Lokantası", "{district} Kebapçısı",
        "Mangal {surname}", "Pide {surname}",
    ],
    "cafe": [
        "{name} Coffee", "{surname} Cafe", "Brew & Bean",
        "Kahve Durağı", "{name}'s Coffee Shop", "Filtre Coffee Lab",
        "The {surname} Cafe", "Espresso House {district}",
        "Roast Republic", "{name} Bakery & Cafe",
        "Artisan Coffee {district}", "Cup of Joy", "Lazy Cat Cafe",
        "Third Wave Coffee", "Caffeine Lab",
    ],
    "clothing_store": [
        "{surname} Giyim", "{name} Fashion", "{name} Butik",
        "Style House {district}", "Urban {surname}", "Chic & Unique",
        "{name} Collection", "Trend {surname}", "Moda Evi {surname}",
        "Elegance Boutique", "Street Style {district}",
        "{surname} Tekstil", "Fashion Point", "La Bella Moda",
        "Silk & Cotton",
    ],
    "electronics_store": [
        "{surname} Elektronik", "Tech Store {district}",
        "{name} Bilişim", "Digital World", "Electro {surname}",
        "{surname} Teknoloji", "Byte Electronics", "Smart Tech {district}",
        "Nano Elektronik", "{name} Computer", "Pixel Electronics",
        "TechZone {district}", "Mega Byte", "Circuit City {district}",
        "E-Store {surname}",
    ],
    "beauty_salon": [
        "{name} Beauty", "{surname} Kuaför", "Beauty Lab {district}",
        "Salon {name}", "{name} Hair Studio", "Glamour {surname}",
        "Style & Beauty {name}", "Elit Güzellik", "The Beauty Room",
        "{name} Spa & Salon", "Hair Art {surname}",
        "Golden Scissors", "Bella Beauty Center", "Charm Kuaför",
        "Prestige Güzellik",
    ],
}

# Category → typical price_level range (1–4)
CATEGORY_PRICE_RANGES = {
    "restaurant":        (1, 4),
    "cafe":              (1, 3),
    "clothing_store":    (2, 4),
    "electronics_store": (2, 4),
    "beauty_salon":      (1, 3),
}

# Category → typical review_count range
CATEGORY_REVIEW_RANGES = {
    "restaurant":        (5, 800),
    "cafe":              (3, 500),
    "clothing_store":    (1, 200),
    "electronics_store": (1, 150),
    "beauty_salon":      (2, 300),
}

# Reviews containing cash/digital payment signals for NLP feature engineering
CASH_SIGNAL_REVIEWS = [
    "Sadece nakit kabul ediyorlar, kart geçmiyor.",
    "Nakit ödeme yapılması gerekiyor, POS cihazı yok.",
    "Maalesef kredi kartı kabul etmiyorlar, peşin ödedik.",
    "Cash only, no credit card accepted.",
    "Nakit indirimi var ama kart yok.",
    "POS cihazı bozuktu, nakit ödedik.",
    "Sadece nakit, biraz garip geldi.",
    "Nakit ödeme zorunlu, ATM'ye gitmek zorunda kaldık.",
]

DIGITAL_SIGNAL_REVIEWS = [
    "Kredi kartıyla rahatça ödeme yaptık.",
    "Temassız ödeme var, çok pratik.",
    "Apple Pay ile ödedim, süper!",
    "Online sipariş ve kartla ödeme imkanı var.",
    "QR kod ile ödeme yapabiliyorsunuz.",
    "Hem nakit hem kart geçiyor, sorunsuz.",
    "Tüm kredi kartları geçerli.",
    "Contactless payment available, very convenient.",
    "Mobil ödeme de kabul ediyorlar.",
]

NEUTRAL_REVIEWS = [
    "Harika bir mekan, çok beğendik!",
    "Hizmet biraz yavaştı ama yemekler güzeldi.",
    "Fiyat-performans açısından gayet iyi.",
    "Personel çok ilgili ve güler yüzlü.",
    "Ortam çok güzel, tekrar geleceğiz.",
    "İdare eder, çok da beklentiye girmeyin.",
    "Kaliteli ürünler, tavsiye ederim.",
    "Çok kalabalıktı, sıra beklettiler.",
    "Mükemmel bir deneyimdi, kesinlikle tavsiye ederim.",
    "Fiyatlar biraz yüksek ama kalite iyi.",
    "Dekorasyon ve ambiyans muhteşem.",
    "Müşteri hizmetleri çok iyi, sorunumuzu hemen çözdüler.",
    "Çeşitlilik az ama olanlar kaliteli.",
    "Konum çok merkezi, ulaşımı kolay.",
    "Temiz ve düzenli bir işletme.",
    "Great place, will definitely come back!",
    "Good quality products and friendly staff.",
    "Reasonable prices for the quality offered.",
]


# ---------------------------------------------------------------------------
# Generator Functions
# ---------------------------------------------------------------------------

def _generate_place_id() -> str:
    """Generate a Google Places-style place_id."""
    return f"ChIJ{uuid.uuid4().hex[:24]}"


def _generate_business_name(category: str, district: str) -> str:
    """Generate a category-appropriate business name using Turkish names."""
    templates = BUSINESS_NAME_TEMPLATES[category]
    template = random.choice(templates)

    first_name = fake.first_name()
    last_name = fake.last_name()

    return template.format(
        name=first_name,
        surname=last_name,
        district=district,
    )


def _jitter_coords(lat: float, lng: float, radius_km: float = 2.0) -> tuple[float, float]:
    """Add random offset to coordinates within a radius (in km)."""
    # ~0.009 degrees latitude ≈ 1 km
    # ~0.012 degrees longitude ≈ 1 km at Istanbul's latitude
    lat_offset = random.uniform(-radius_km, radius_km) * 0.009
    lng_offset = random.uniform(-radius_km, radius_km) * 0.012
    return round(lat + lat_offset, 6), round(lng + lng_offset, 6)


def _generate_rating() -> float:
    """Generate a realistic Google Maps rating (skewed toward 3.5–4.5)."""
    # Use a beta distribution to skew toward higher ratings
    raw = random.betavariate(5, 2)  # mean ~0.71
    rating = 1.0 + raw * 4.0       # scale to 1.0–5.0
    return round(min(5.0, max(1.0, rating)), 1)


def _generate_reviews(category: str, count: int = 5) -> str:
    """
    Generate a set of mock reviews with occasional cash/digital signals.

    Distribution:
    - ~60% neutral reviews
    - ~25% cash signal reviews (business might need POS)
    - ~15% digital signal reviews (business already has POS)
    """
    reviews = []
    for _ in range(count):
        roll = random.random()
        if roll < 0.25:
            reviews.append(random.choice(CASH_SIGNAL_REVIEWS))
        elif roll < 0.40:
            reviews.append(random.choice(DIGITAL_SIGNAL_REVIEWS))
        else:
            reviews.append(random.choice(NEUTRAL_REVIEWS))
    return " | ".join(reviews)


def generate_merchant(category: str | None = None, district: str | None = None) -> dict:
    """
    Generate a single realistic mock merchant record.

    Args:
        category: Force a specific category, or random if None.
        district: Force a specific district, or random if None.

    Returns:
        Dictionary matching the Merchant ORM model fields.
    """
    if category is None:
        category = random.choice(TARGET_CATEGORIES)
    if district is None:
        district = random.choice(list(ISTANBUL_DISTRICTS.keys()))

    center_lat, center_lng = ISTANBUL_DISTRICTS[district]
    lat, lng = _jitter_coords(center_lat, center_lng)

    price_lo, price_hi = CATEGORY_PRICE_RANGES[category]
    review_lo, review_hi = CATEGORY_REVIEW_RANGES[category]

    # Some merchants don't have price_level set (~20%)
    price_level = random.randint(price_lo, price_hi) if random.random() > 0.2 else None

    review_count = random.randint(review_lo, review_hi)

    # Website/phone probability varies by category
    has_website = random.random() < {
        "restaurant": 0.45,
        "cafe": 0.55,
        "clothing_store": 0.65,
        "electronics_store": 0.80,
        "beauty_salon": 0.40,
    }[category]

    has_phone = random.random() < 0.85  # Most businesses have a phone

    # Generate reviews — more reviews for higher review_count
    num_review_texts = min(10, max(3, review_count // 30))
    reviews_text = _generate_reviews(category, count=num_review_texts)

    return {
        "place_id": _generate_place_id(),
        "name": _generate_business_name(category, district),
        "category": category,
        "latitude": lat,
        "longitude": lng,
        "address": f"{fake.street_address()}, {district}, İstanbul",
        "district": district,
        "rating": _generate_rating(),
        "review_count": review_count,
        "price_level": price_level,
        "has_website": has_website,
        "has_phone": has_phone,
        "reviews_text": reviews_text,
    }


def generate_merchants(count: int = 250) -> list[dict]:
    """
    Generate multiple merchants with balanced category and district distribution.

    Ensures:
    - Each category gets at least count // len(categories) merchants
    - Each district gets at least count // len(districts) merchants
    - Remaining merchants are fully random
    """
    merchants = []
    categories = TARGET_CATEGORIES
    districts = list(ISTANBUL_DISTRICTS.keys())

    # Phase 1: Ensure minimum per-category coverage
    per_category = count // len(categories)
    for cat in categories:
        for _ in range(per_category):
            district = random.choice(districts)
            merchants.append(generate_merchant(category=cat, district=district))

    # Phase 2: Fill remaining with random combinations
    remaining = count - len(merchants)
    for _ in range(remaining):
        merchants.append(generate_merchant())

    # Shuffle to avoid ordered blocks
    random.shuffle(merchants)

    return merchants


def seed_database(count: int = 250) -> int:
    """
    Generate mock merchants and insert them into the database.

    Returns:
        Number of merchants inserted.
    """
    import sys
    import os
    # Ensure backend/ is on the path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from database import SessionLocal, init_db
    from models import Merchant

    # Create tables if they don't exist
    init_db()

    merchants = generate_merchants(count)
    session = SessionLocal()

    try:
        # Clear existing mock data
        session.query(Merchant).delete()
        session.commit()

        # Bulk insert
        db_merchants = [Merchant(**m) for m in merchants]
        session.add_all(db_merchants)
        session.commit()

        print(f"[OK] Inserted {len(db_merchants)} merchants into the database.")

        # Print distribution summary
        _print_summary(merchants)

        return len(db_merchants)

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Error inserting merchants: {e}")
        raise
    finally:
        session.close()


def _print_summary(merchants: list[dict]) -> None:
    """Print a summary of the generated data distribution."""
    from collections import Counter

    cat_counts = Counter(m["category"] for m in merchants)
    dist_counts = Counter(m["district"] for m in merchants)
    ratings = [m["rating"] for m in merchants]
    website_count = sum(1 for m in merchants if m["has_website"])
    phone_count = sum(1 for m in merchants if m["has_phone"])

    print(f"\n{'='*50}")
    print(f"  Mock Data Summary")
    print(f"{'='*50}")
    print(f"  Total merchants: {len(merchants)}")
    print(f"  Avg rating:      {sum(ratings)/len(ratings):.1f}")
    print(f"  Has website:     {website_count} ({website_count/len(merchants)*100:.0f}%)")
    print(f"  Has phone:       {phone_count} ({phone_count/len(merchants)*100:.0f}%)")
    print(f"\n  Category Distribution:")
    for cat, cnt in sorted(cat_counts.items()):
        print(f"    {cat:20s} -> {cnt}")
    print(f"\n  District Distribution:")
    for dist, cnt in sorted(dist_counts.items()):
        print(f"    {dist:20s} -> {cnt}")
    print(f"{'='*50}\n")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate mock merchant data for Moka Fit Score")
    parser.add_argument("--count", type=int, default=250, help="Number of merchants to generate (default: 250)")
    args = parser.parse_args()

    seed_database(count=args.count)
