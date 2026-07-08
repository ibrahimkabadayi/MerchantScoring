"""
Moka Fit Score — Feature Engineering

Transforms raw merchant data into the feature vector consumed by the scoring model.

Features produced:
  - rating                 : Google Maps rating (1.0-5.0)
  - review_count           : Total number of reviews
  - price_level            : Price tier (1-4)
  - has_website            : Binary (0/1)
  - has_phone              : Binary (0/1)
  - category_encoded       : Label-encoded business category
  - district_density       : Normalized business density of the district (0-1)
  - cash_signal_score      : NLP score from reviews (-1 = cash-heavy, +1 = digital-ready)
  - sector_growth_index    : Sector-level growth coefficient
  - review_recency_score   : Simulated recency of reviews (0-1)
"""

import re
import random

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Keywords for NLP cash/digital signal detection
CASH_KEYWORDS = [
    "nakit", "cash", "pesin", "peşin", "nakit odeme", "nakit ödeme",
    "pos yok", "kart yok", "kart gecmiyor", "kart geçmiyor",
    "cash only", "no credit card", "no card",
]

DIGITAL_KEYWORDS = [
    "kart", "kredi karti", "kredi kartı", "temassiz", "temassız",
    "qr", "online odeme", "online ödeme", "contactless",
    "apple pay", "mobil odeme", "mobil ödeme",
    "kart geciyor", "kart geçiyor",
]

# Sector growth indices (higher = faster-growing sector for POS adoption)
SECTOR_GROWTH_INDEX = {
    "restaurant":        0.15,
    "cafe":              0.22,
    "clothing_store":    0.10,
    "electronics_store": 0.08,
    "beauty_salon":      0.18,
}

# Approximate business density per Istanbul district (normalized 0-1)
# Based on typical commercial activity levels
DISTRICT_DENSITY = {
    "Beyoğlu":    0.95,
    "Kadıköy":    0.88,
    "Beşiktaş":   0.85,
    "Şişli":      0.90,
    "Bakırköy":   0.72,
    "Üsküdar":    0.65,
    "Fatih":      0.78,
    "Sarıyer":    0.45,
    "Maltepe":    0.50,
    "Ataşehir":   0.70,
    "Kartal":     0.42,
    "Pendik":     0.38,
}

# Category label encoding (deterministic order)
CATEGORY_ORDER = [
    "beauty_salon",
    "cafe",
    "clothing_store",
    "electronics_store",
    "restaurant",
]

# ---------------------------------------------------------------------------
# NLP: Cash/Digital Signal Scoring
# ---------------------------------------------------------------------------

def compute_cash_signal_score(reviews_text: str | None) -> float:
    """
    Analyze review text for cash vs. digital payment signals.

    Returns:
        Float between -1.0 (strongly cash-oriented) and +1.0 (strongly digital-ready).
        Returns 0.0 if no signals are found or reviews_text is empty.
    """
    if not reviews_text:
        return 0.0

    text_lower = reviews_text.lower()

    cash_hits = sum(1 for kw in CASH_KEYWORDS if kw in text_lower)
    digital_hits = sum(1 for kw in DIGITAL_KEYWORDS if kw in text_lower)

    total = cash_hits + digital_hits
    if total == 0:
        return 0.0

    # Score ranges from -1 (all cash) to +1 (all digital)
    score = (digital_hits - cash_hits) / total
    return round(score, 4)


# ---------------------------------------------------------------------------
# Feature Vector Construction
# ---------------------------------------------------------------------------

def engineer_features(merchants_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform a DataFrame of raw merchant data into a feature matrix.

    Args:
        merchants_df: DataFrame with columns matching the Merchant ORM model.

    Returns:
        DataFrame with engineered feature columns, indexed by place_id.
    """
    df = merchants_df.copy()

    # --- Category encoding ---
    cat_map = {cat: idx for idx, cat in enumerate(CATEGORY_ORDER)}
    df["category_encoded"] = df["category"].map(cat_map).fillna(0).astype(int)

    # --- District density ---
    df["district_density"] = df["district"].map(DISTRICT_DENSITY).fillna(0.5)

    # --- Cash signal score (NLP) ---
    df["cash_signal_score"] = df["reviews_text"].apply(compute_cash_signal_score)

    # --- Sector growth index ---
    df["sector_growth_index"] = df["category"].map(SECTOR_GROWTH_INDEX).fillna(0.1)

    # --- Review recency score ---
    # In production this would use actual review timestamps.
    # For mock data, we simulate based on review_count (more reviews = more recent activity).
    max_reviews = df["review_count"].max() if df["review_count"].max() > 0 else 1
    df["review_recency_score"] = (
        df["review_count"].fillna(0) / max_reviews
    ).clip(0, 1).round(4)

    # Add small random noise to avoid identical recency scores
    np.random.seed(42)
    noise = np.random.uniform(-0.05, 0.05, size=len(df))
    df["review_recency_score"] = (df["review_recency_score"] + noise).clip(0, 1).round(4)

    # --- Boolean to int ---
    df["has_website"] = df["has_website"].astype(int)
    df["has_phone"] = df["has_phone"].astype(int)

    # --- Select final feature columns ---
    feature_columns = [
        "place_id",
        "rating",
        "review_count",
        "price_level",
        "has_website",
        "has_phone",
        "category_encoded",
        "district_density",
        "cash_signal_score",
        "sector_growth_index",
        "review_recency_score",
    ]

    result = df[feature_columns].copy()
    result = result.set_index("place_id")

    return result


def get_feature_columns() -> list[str]:
    """Return the ordered list of feature column names (excluding place_id index)."""
    return [
        "rating",
        "review_count",
        "price_level",
        "has_website",
        "has_phone",
        "category_encoded",
        "district_density",
        "cash_signal_score",
        "sector_growth_index",
        "review_recency_score",
    ]
