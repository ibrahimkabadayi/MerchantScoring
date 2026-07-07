"""
Moka Fit Score — SQLAlchemy ORM Models

Defines the Merchant table that stores raw data, engineered features,
and computed Moka Fit Scores.
"""

from datetime import datetime, timezone

from sqlalchemy import String, Float, Integer, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Merchant(Base):
    """A merchant (business) record with raw data and scoring results."""

    __tablename__ = "merchants"

    # --- Identity ---
    place_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)

    # --- Location ---
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # --- Raw attributes ---
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_website: Mapped[bool] = mapped_column(Boolean, default=False)
    has_phone: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Raw text (for NLP) ---
    reviews_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Moka Fit Score ---
    moka_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    digital_readiness: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth_momentum: Mapped[float | None] = mapped_column(Float, nullable=True)
    reachability: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector_fit: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority_tier: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # --- Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Merchant place_id={self.place_id!r} name={self.name!r} "
            f"score={self.moka_fit_score} tier={self.priority_tier!r}>"
        )
