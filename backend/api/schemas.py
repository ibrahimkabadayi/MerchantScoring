"""
Moka Fit Score — Pydantic Schemas

Request/response models for the FastAPI endpoints.
"""

from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    """Detailed sub-scores that compose the Moka Fit Score."""
    digital_readiness: float
    growth_momentum: float
    reachability: float
    sector_fit: float


class MerchantResponse(BaseModel):
    """Full merchant representation returned by the API."""
    place_id: str
    name: str
    category: str
    latitude: float
    longitude: float
    address: str | None = None
    district: str | None = None
    rating: float | None = None
    review_count: int | None = None
    price_level: int | None = None
    has_website: bool = False
    has_phone: bool = False
    moka_fit_score: float | None = None
    score_breakdown: ScoreBreakdown | None = None
    priority_tier: str | None = None

    model_config = {"from_attributes": True}


class MerchantListResponse(BaseModel):
    """Paginated list of merchants."""
    total: int
    merchants: list[MerchantResponse]


class StatsResponse(BaseModel):
    """Dashboard summary statistics."""
    total_merchants: int
    high_count: int
    medium_count: int
    low_count: int
    avg_score: float
    category_distribution: dict[str, int]
    district_distribution: dict[str, int]


class OutreachRequest(BaseModel):
    """Request body for outreach message generation."""
    place_id: str


class OutreachResponse(BaseModel):
    """Generated outreach message for a merchant."""
    place_id: str
    merchant_name: str
    message: str
