"""
Moka Fit Score — Model Trainer

Trains an XGBoost binary classifier using synthetic labels to predict
whether a merchant is a good fit for Moka's POS solutions.

Synthetic label logic (since we have no real conversion data):
  A merchant is labeled POSITIVE (good fit) when:
    - rating >= 3.5 (established business)
    - has_website OR has_phone (reachable)
    - cash_signal_score < 0 (cash-heavy -> needs POS)
    - price_level >= 2 (medium+ price tier)
  The label is probabilistic: the more criteria met, the higher the
  probability of being labeled positive (with added noise).

Usage:
    python -m model.trainer
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, init_db
from models import Merchant
from features.engineer import engineer_features, get_feature_columns
from features.preprocessor import preprocess

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Synthetic Label Generation
# ---------------------------------------------------------------------------

def generate_synthetic_labels(merchants_df: pd.DataFrame, features_df: pd.DataFrame) -> pd.Series:
    """
    Generate synthetic binary labels based on business heuristics.

    A merchant scores points for each criterion met:
      +1  rating >= 3.5
      +1  has_website or has_phone
      +1  cash_signal_score < 0 (cash-heavy = POS opportunity)
      +1  price_level >= 2
      +0.5 review_count > median

    The total is converted to a probability, and a Bernoulli draw gives the label.
    """
    np.random.seed(42)

    df = features_df.copy()

    # Align with raw data for fields not in features
    raw = merchants_df.set_index("place_id")

    scores = pd.Series(0.0, index=df.index)

    # Criterion 1: Established business
    scores += (df["rating"] >= 3.5).astype(float) * 1.0

    # Criterion 2: Reachable
    scores += ((df["has_website"] == 1) | (df["has_phone"] == 1)).astype(float) * 1.0

    # Criterion 3: Cash-heavy (needs POS)
    scores += (df["cash_signal_score"] < 0).astype(float) * 1.0

    # Criterion 4: Medium+ price tier
    scores += (df["price_level"] >= 2).astype(float) * 1.0

    # Criterion 5: Active business (above-median reviews)
    median_reviews = df["review_count"].median()
    scores += (df["review_count"] > median_reviews).astype(float) * 0.5

    # Convert to probability [0.1, 0.9] and draw labels
    max_score = 4.5
    probabilities = 0.1 + (scores / max_score) * 0.8
    labels = (np.random.random(len(df)) < probabilities).astype(int)

    return labels


# ---------------------------------------------------------------------------
# Training Pipeline
# ---------------------------------------------------------------------------

def train_model() -> dict:
    """
    Full training pipeline:
      1. Load merchants from DB
      2. Engineer features
      3. Preprocess (impute + normalize)
      4. Generate synthetic labels
      5. Train XGBoost
      6. Evaluate and log metrics
      7. Save model + scaler artifacts

    Returns:
        Dictionary with training metrics and artifact paths.
    """
    print("=" * 60)
    print("  Moka Fit Score — Model Training")
    print("=" * 60)

    # --- 1. Load data ---
    print("\n[1/7] Loading merchants from database...")
    session = SessionLocal()
    try:
        merchants = session.query(Merchant).all()
        if not merchants:
            raise ValueError("No merchants in database. Run mock_generator first.")

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
        } for m in merchants])
        print(f"    Loaded {len(merchants_df)} merchants.")
    finally:
        session.close()

    # --- 2. Feature engineering ---
    print("[2/7] Engineering features...")
    features_df = engineer_features(merchants_df)
    print(f"    Feature matrix shape: {features_df.shape}")

    # --- 3. Preprocessing ---
    print("[3/7] Preprocessing (impute + normalize)...")
    processed_df, scaler = preprocess(features_df)
    print(f"    Features after preprocessing: {list(processed_df.columns)}")

    # --- 4. Synthetic labels ---
    print("[4/7] Generating synthetic labels...")
    labels = generate_synthetic_labels(merchants_df, features_df)
    positive_rate = labels.mean()
    print(f"    Positive rate: {positive_rate:.1%} ({labels.sum()}/{len(labels)})")

    # --- 5. Train/test split ---
    print("[5/7] Splitting train/test (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        processed_df, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"    Train: {len(X_train)} | Test: {len(X_test)}")

    # --- 6. Train XGBoost ---
    print("[6/7] Training XGBoost classifier...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss",
        use_label_encoder=False,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # --- 7. Evaluate ---
    print("[7/7] Evaluating model...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    report = classification_report(y_test, y_pred, output_dict=True)
    auc_score = roc_auc_score(y_test, y_prob)

    print(f"\n    AUC-ROC: {auc_score:.4f}")
    print(f"    Accuracy: {report['accuracy']:.4f}")
    print(f"    Precision (pos): {report['1']['precision']:.4f}")
    print(f"    Recall (pos): {report['1']['recall']:.4f}")
    print(f"    F1 (pos): {report['1']['f1-score']:.4f}")

    # Feature importance
    feature_names = get_feature_columns()
    importances = dict(zip(feature_names, model.feature_importances_.tolist()))
    sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)

    print("\n    Feature Importance:")
    for fname, imp in sorted_imp:
        bar = "#" * int(imp * 40)
        print(f"      {fname:25s} {imp:.4f} {bar}")

    # --- Save artifacts ---
    model_path = ARTIFACTS_DIR / "xgb_model.pkl"
    scaler_path = ARTIFACTS_DIR / "scaler.pkl"
    meta_path = ARTIFACTS_DIR / "training_meta.json"

    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_merchants": len(merchants_df),
        "n_features": len(feature_names),
        "feature_names": feature_names,
        "positive_rate": round(positive_rate, 4),
        "auc_roc": round(auc_score, 4),
        "accuracy": round(report["accuracy"], 4),
        "feature_importance": {k: round(v, 4) for k, v in sorted_imp},
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n    Artifacts saved:")
    print(f"      Model:    {model_path}")
    print(f"      Scaler:   {scaler_path}")
    print(f"      Metadata: {meta_path}")
    print("=" * 60)

    return meta


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    train_model()
