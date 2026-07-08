"""
Moka Fit Score — Data Preprocessor

Handles missing value imputation and feature normalization before model training.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

from features.engineer import get_feature_columns


def impute_missing_values(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill missing values using appropriate strategies per column.

    Strategy:
      - rating:       median (most common Google Maps behavior)
      - review_count: 0 (no reviews = 0)
      - price_level:  median (missing price_level is common on Google Maps)
      - All others:   0 (binary/encoded fields shouldn't be missing)
    """
    df = features_df.copy()

    # Numeric columns with specific strategies
    if "rating" in df.columns:
        df["rating"] = df["rating"].fillna(df["rating"].median())

    if "review_count" in df.columns:
        df["review_count"] = df["review_count"].fillna(0)

    if "price_level" in df.columns:
        df["price_level"] = df["price_level"].fillna(df["price_level"].median())

    # Fill any remaining NaN with 0
    df = df.fillna(0)

    return df


def normalize_features(features_df: pd.DataFrame) -> tuple[pd.DataFrame, MinMaxScaler]:
    """
    Apply Min-Max normalization to scale all features to [0, 1].

    Args:
        features_df: DataFrame with imputed feature values.

    Returns:
        Tuple of (normalized DataFrame, fitted MinMaxScaler).
    """
    scaler = MinMaxScaler()
    columns = features_df.columns.tolist()

    scaled_values = scaler.fit_transform(features_df)
    normalized_df = pd.DataFrame(scaled_values, columns=columns, index=features_df.index)

    return normalized_df, scaler


def preprocess(features_df: pd.DataFrame) -> tuple[pd.DataFrame, MinMaxScaler]:
    """
    Full preprocessing pipeline: impute -> normalize.

    Args:
        features_df: Raw feature DataFrame from engineer.py.

    Returns:
        Tuple of (preprocessed DataFrame, fitted scaler).
    """
    imputed = impute_missing_values(features_df)
    normalized, scaler = normalize_features(imputed)
    return normalized, scaler
