"""
Moka Fit Score — Scorer

Loads the trained XGBoost model and computes Moka Fit Scores (0-100)
with sub-score breakdowns for each merchant.

Score Components (weighted):
  - digital_readiness  (25%): has_website, has_phone, cash_signal_score
  - growth_momentum    (20%): review_count, review_recency_score
  - reachability       (20%): has_phone, has_website, address completeness
  - sector_fit         (20%): category fit, price_level, sector_growth_index
  - district_density   (15%): business density of the district

Priority Tiers:
  - HIGH   : score >= 70
  - MEDIUM : score >= 45
  - LOW    : score < 45
"""

import sys
import os
from pathlib import Path

import pandas as pd
import numpy as np
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from features.engineer import engineer_features, get_feature_columns
from features.preprocessor import impute_missing_values

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


class MokaScorer:
    """Loads trained model artifacts and scores merchants."""

    def __init__(self):
        model_path = ARTIFACTS_DIR / "xgb_model.pkl"
        scaler_path = ARTIFACTS_DIR / "scaler.pkl"

        if not model_path.exists() or not scaler_path.exists():
            raise FileNotFoundError(
                "Model artifacts not found. Run `python -m model.trainer` first."
            )

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.feature_columns = get_feature_columns()

    def score_merchants(self, merchants_df: pd.DataFrame) -> pd.DataFrame:
        """
        Score a DataFrame of merchants.

        Args:
            merchants_df: DataFrame with raw merchant columns.

        Returns:
            DataFrame with added columns: moka_fit_score, digital_readiness,
            growth_momentum, reachability, sector_fit, priority_tier.
        """
        # Engineer features
        features = engineer_features(merchants_df)

        # Impute missing values (same strategy as training)
        features = impute_missing_values(features)

        # Keep raw features for sub-score calculation before normalization
        raw_features = features.copy()

        # Normalize using the trained scaler
        scaled = pd.DataFrame(
            self.scaler.transform(features),
            columns=features.columns,
            index=features.index,
        )

        # Get model probability (probability of being a good Moka fit)
        proba = self.model.predict_proba(scaled)[:, 1]

        # Convert probability to 0-100 score
        moka_scores = np.round(proba * 100, 1)

        # Compute sub-score breakdowns using raw features
        breakdowns = self._compute_breakdowns(raw_features)

        # Build result DataFrame
        result = merchants_df.copy()
        result = result.set_index("place_id")

        result["moka_fit_score"] = moka_scores
        result["digital_readiness"] = breakdowns["digital_readiness"]
        result["growth_momentum"] = breakdowns["growth_momentum"]
        result["reachability"] = breakdowns["reachability"]
        result["sector_fit"] = breakdowns["sector_fit"]
        result["priority_tier"] = pd.Series(moka_scores, index=features.index).apply(
            self._assign_tier
        )

        result = result.reset_index()
        return result

    def _compute_breakdowns(self, features: pd.DataFrame) -> dict[str, pd.Series]:
        """
        Compute the four sub-scores (each 0-100) from raw feature values.

        These are heuristic scores meant for explainability, not model inputs.
        """
        idx = features.index

        # --- Digital Readiness (25% weight in overall) ---
        # Components: has_website, has_phone, cash_signal_score (inverted: low = needs POS = opportunity)
        digital = (
            features["has_website"] * 35
            + features["has_phone"] * 25
            # Invert cash_signal: -1 (cash) -> 40, +1 (digital) -> 0
            + (1 - features["cash_signal_score"]) / 2 * 40
        ).clip(0, 100).round(0)

        # --- Growth Momentum (20%) ---
        # Components: review_count (log-scaled), review_recency_score
        max_reviews = features["review_count"].max() if features["review_count"].max() > 0 else 1
        log_reviews = np.log1p(features["review_count"]) / np.log1p(max_reviews)
        growth = (
            log_reviews * 55
            + features["review_recency_score"] * 45
        ).clip(0, 100).round(0)

        # --- Reachability (20%) ---
        # Components: has_phone, has_website (different weights than digital_readiness)
        reach = (
            features["has_phone"] * 45
            + features["has_website"] * 40
            + features["district_density"] * 15
        ).clip(0, 100).round(0)

        # --- Sector Fit (20%) ---
        # Components: price_level, sector_growth_index
        price_norm = features["price_level"].clip(1, 4) / 4
        sector_growth_norm = features["sector_growth_index"] / 0.25  # max is ~0.22
        sector = (
            price_norm * 50
            + sector_growth_norm.clip(0, 1) * 50
        ).clip(0, 100).round(0)

        return {
            "digital_readiness": digital,
            "growth_momentum": growth,
            "reachability": reach,
            "sector_fit": sector,
        }

    @staticmethod
    def _assign_tier(score: float) -> str:
        """Assign priority tier based on Moka Fit Score."""
        if score >= 70:
            return "HIGH"
        elif score >= 45:
            return "MEDIUM"
        return "LOW"


# ---------------------------------------------------------------------------
# Bulk scoring utility
# ---------------------------------------------------------------------------

def score_and_update_db() -> int:
    """
    Load all merchants from DB, score them, and update score columns.

    Returns:
        Number of merchants scored.
    """
    from database import SessionLocal, init_db
    from models import Merchant

    init_db()
    session = SessionLocal()

    try:
        merchants = session.query(Merchant).all()
        if not merchants:
            print("[ERROR] No merchants found in database.")
            return 0

        # Convert to DataFrame
        merchants_df = pd.DataFrame([{
            "place_id": m.place_id,
            "name": m.name,
            "category": m.category,
            "rating": m.rating,
            "review_count": m.review_count,
            "price_level": m.price_level,
            "has_website": m.has_website,
            "has_phone": m.has_phone,
            "district": m.district,
            "reviews_text": m.reviews_text,
            "latitude": m.latitude,
            "longitude": m.longitude,
            "address": m.address,
        } for m in merchants])

        # Score
        scorer = MokaScorer()
        scored_df = scorer.score_merchants(merchants_df)

        # Update DB
        for _, row in scored_df.iterrows():
            merchant = session.query(Merchant).filter(
                Merchant.place_id == row["place_id"]
            ).first()
            if merchant:
                merchant.moka_fit_score = float(row["moka_fit_score"])
                merchant.digital_readiness = float(row["digital_readiness"])
                merchant.growth_momentum = float(row["growth_momentum"])
                merchant.reachability = float(row["reachability"])
                merchant.sector_fit = float(row["sector_fit"])
                merchant.priority_tier = row["priority_tier"]

        session.commit()
        print(f"[OK] Scored and updated {len(scored_df)} merchants in database.")

        # Print tier distribution
        tier_counts = scored_df["priority_tier"].value_counts()
        avg_score = scored_df["moka_fit_score"].mean()
        print(f"\n    Average Moka Fit Score: {avg_score:.1f}")
        print(f"    Tier Distribution:")
        for tier in ["HIGH", "MEDIUM", "LOW"]:
            count = tier_counts.get(tier, 0)
            print(f"      {tier:8s} -> {count}")

        return len(scored_df)

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Scoring failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    score_and_update_db()
