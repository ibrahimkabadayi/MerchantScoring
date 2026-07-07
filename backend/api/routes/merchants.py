"""
Moka Fit Score — Merchant API Routes

Endpoints for listing, filtering, and retrieving scored merchants.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database import get_db
from models import Merchant
from api.schemas import MerchantResponse, MerchantListResponse, ScoreBreakdown, StatsResponse

router = APIRouter(prefix="/api/merchants", tags=["merchants"])


def _merchant_to_response(m: Merchant) -> MerchantResponse:
    """Convert an ORM Merchant to a MerchantResponse with score breakdown."""
    breakdown = None
    if m.moka_fit_score is not None:
        breakdown = ScoreBreakdown(
            digital_readiness=m.digital_readiness or 0,
            growth_momentum=m.growth_momentum or 0,
            reachability=m.reachability or 0,
            sector_fit=m.sector_fit or 0,
        )
    return MerchantResponse(
        place_id=m.place_id,
        name=m.name,
        category=m.category,
        latitude=m.latitude,
        longitude=m.longitude,
        address=m.address,
        district=m.district,
        rating=m.rating,
        review_count=m.review_count,
        price_level=m.price_level,
        has_website=m.has_website,
        has_phone=m.has_phone,
        moka_fit_score=m.moka_fit_score,
        score_breakdown=breakdown,
        priority_tier=m.priority_tier,
    )


@router.get("", response_model=MerchantListResponse)
def list_merchants(
    tier: str | None = Query(None, description="Filter by priority tier (HIGH, MEDIUM, LOW)"),
    category: str | None = Query(None, description="Filter by business category"),
    district: str | None = Query(None, description="Filter by district name"),
    min_score: float | None = Query(None, ge=0, le=100, description="Minimum Moka Fit Score"),
    sort_by: str = Query("score", description="Sort field: score, rating, review_count, name"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List all scored merchants with optional filters and sorting."""
    query = db.query(Merchant)

    # Apply filters
    if tier:
        query = query.filter(Merchant.priority_tier == tier.upper())
    if category:
        query = query.filter(Merchant.category == category)
    if district:
        query = query.filter(Merchant.district == district)
    if min_score is not None:
        query = query.filter(Merchant.moka_fit_score >= min_score)

    # Total count before pagination
    total = query.count()

    # Sorting
    sort_map = {
        "score": desc(Merchant.moka_fit_score),
        "rating": desc(Merchant.rating),
        "review_count": desc(Merchant.review_count),
        "name": Merchant.name,
    }
    order = sort_map.get(sort_by, desc(Merchant.moka_fit_score))
    query = query.order_by(order)

    # Pagination
    merchants = query.offset(offset).limit(limit).all()

    return MerchantListResponse(
        total=total,
        merchants=[_merchant_to_response(m) for m in merchants],
    )


@router.get("/top", response_model=list[MerchantResponse])
def top_merchants(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get the top N merchants by Moka Fit Score."""
    merchants = (
        db.query(Merchant)
        .filter(Merchant.moka_fit_score.isnot(None))
        .order_by(desc(Merchant.moka_fit_score))
        .limit(limit)
        .all()
    )
    return [_merchant_to_response(m) for m in merchants]


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Dashboard summary statistics."""
    total = db.query(Merchant).count()
    high = db.query(Merchant).filter(Merchant.priority_tier == "HIGH").count()
    medium = db.query(Merchant).filter(Merchant.priority_tier == "MEDIUM").count()
    low = db.query(Merchant).filter(Merchant.priority_tier == "LOW").count()

    avg = db.query(func.avg(Merchant.moka_fit_score)).scalar() or 0.0

    # Category distribution
    cat_rows = (
        db.query(Merchant.category, func.count())
        .group_by(Merchant.category)
        .all()
    )
    category_dist = {row[0]: row[1] for row in cat_rows}

    # District distribution
    dist_rows = (
        db.query(Merchant.district, func.count())
        .filter(Merchant.district.isnot(None))
        .group_by(Merchant.district)
        .all()
    )
    district_dist = {row[0]: row[1] for row in dist_rows}

    return StatsResponse(
        total_merchants=total,
        high_count=high,
        medium_count=medium,
        low_count=low,
        avg_score=round(avg, 1),
        category_distribution=category_dist,
        district_distribution=district_dist,
    )


@router.get("/{place_id}", response_model=MerchantResponse)
def get_merchant(place_id: str, db: Session = Depends(get_db)):
    """Get a single merchant by place_id."""
    merchant = db.query(Merchant).filter(Merchant.place_id == place_id).first()
    if not merchant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Merchant not found")
    return _merchant_to_response(merchant)
