"""
Moka Fit Score — Outreach API Routes

Endpoint for generating personalized outreach messages via Gemini LLM.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Merchant
from api.schemas import OutreachRequest, OutreachResponse

router = APIRouter(prefix="/api/outreach", tags=["outreach"])


@router.post("/generate", response_model=OutreachResponse)
async def generate_outreach(
    request: OutreachRequest,
    db: Session = Depends(get_db),
):
    """Generate a personalized outreach message for a merchant using Gemini."""
    merchant = db.query(Merchant).filter(Merchant.place_id == request.place_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    # Lazy import to avoid loading LLM module on startup
    from outreach.generator import generate_outreach_message

    message = await generate_outreach_message(merchant)

    return OutreachResponse(
        place_id=merchant.place_id,
        merchant_name=merchant.name,
        message=message,
    )
