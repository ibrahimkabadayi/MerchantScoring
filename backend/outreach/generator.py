"""
Moka Fit Score — Outreach Message Generator

Generates personalized outreach messages using Google Gemini API.
Falls back to a template-based message if Gemini is unavailable.
"""

import logging
from google import genai
from google.genai import types

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini Client (lazy-initialized)
# ---------------------------------------------------------------------------

_client: genai.Client | None = None


def _get_client() -> genai.Client | None:
    """Return a Gemini client, or None if no API key is configured."""
    global _client
    if _client is not None:
        return _client

    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.warning("GEMINI_API_KEY not configured — using template fallback.")
        return None

    _client = genai.Client(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Prompt Construction
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Moka United's sales assistant.
Your job: write a short, friendly, and persuasive first-contact message
for the given business profile.

Rules:
- Maximum 3 paragraphs
- Match the tone to the business category and size
- Highlight Moka's value proposition (fast setup, low commission, 24/7 support)
- Mention a standout trait of the business (rating, review count, growth)
- Write in Turkish
- Do NOT use generic greetings like "Degerli isletme sahibi"
- Address the business by name
- Be specific — reference their category, district, or online presence
- End with a clear call-to-action (meeting, demo, or phone call)
"""


def _build_user_prompt(merchant) -> str:
    """Build the merchant-context prompt for Gemini."""
    # Determine digital presence description
    digital_parts = []
    if merchant.has_website:
        digital_parts.append("Has a website")
    else:
        digital_parts.append("No website")
    if merchant.has_phone:
        digital_parts.append("Has phone listing")
    else:
        digital_parts.append("No phone listing")
    digital_presence = ", ".join(digital_parts)

    # Score breakdown if available
    score_section = ""
    if merchant.moka_fit_score is not None:
        score_section = f"""
Moka Fit Score: {merchant.moka_fit_score:.1f}/100
Score Breakdown:
  - Digital Readiness: {merchant.digital_readiness:.0f}/100
  - Growth Momentum: {merchant.growth_momentum:.0f}/100
  - Reachability: {merchant.reachability:.0f}/100
  - Sector Fit: {merchant.sector_fit:.0f}/100
Priority Tier: {merchant.priority_tier}"""

    # Category display name
    category_display = {
        "restaurant": "Restaurant",
        "cafe": "Cafe / Coffee Shop",
        "clothing_store": "Clothing & Fashion",
        "electronics_store": "Electronics & Technology",
        "beauty_salon": "Beauty & Hair Salon",
    }.get(merchant.category, merchant.category)

    return f"""Business Name: {merchant.name}
Category: {category_display}
Rating: {merchant.rating} ({merchant.review_count} reviews)
Location: {merchant.district}, Istanbul
Price Level: {merchant.price_level or 'Unknown'}/4
Digital Presence: {digital_presence}
{score_section}

Write a first-contact outreach message for this business."""


# ---------------------------------------------------------------------------
# Message Generation
# ---------------------------------------------------------------------------

MODEL_NAME = "gemini-2.0-flash"


async def generate_outreach_message(merchant) -> str:
    """
    Generate a personalized outreach message for the given merchant.

    Uses Google Gemini API if configured, otherwise falls back to a
    template-based message.

    Args:
        merchant: A Merchant ORM instance.

    Returns:
        The generated outreach message string.
    """
    client = _get_client()

    if client is None:
        return _fallback_template(merchant)

    try:
        user_prompt = _build_user_prompt(merchant)

        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                max_output_tokens=500,
                top_p=0.9,
            ),
        )

        message = response.text
        if not message or not message.strip():
            logger.warning(f"Empty Gemini response for {merchant.place_id}, using fallback.")
            return _fallback_template(merchant)

        return message.strip()

    except Exception as e:
        logger.error(f"Gemini API error for {merchant.place_id}: {e}")
        return _fallback_template(merchant)


# ---------------------------------------------------------------------------
# Template Fallback
# ---------------------------------------------------------------------------

# Category-specific value propositions
_CATEGORY_HOOKS = {
    "restaurant": "restoran sektorunde hizli ve guvenilir odeme cozumleriyle musteri memnuniyetinizi artirabilirsiniz",
    "cafe": "kafe ve kahve dunyasinda temassiz odeme ve hizli islem ozellikleriyle musterilerinize modern bir deneyim sunabilirsiniz",
    "clothing_store": "moda ve giyim sektorunde taksitli odeme secenekleri ve dusuk komisyon oranlariyla satis hacminizi artirabilirsiniz",
    "electronics_store": "teknoloji sektorunde yuksek tutarli islemlerde taksit secenekleri ve guvenli odeme altyapisiyla musterilerinize esneklik sunabilirsiniz",
    "beauty_salon": "guzellik ve bakim sektorunde randevu bazli odemeleri kolaylastiran ve musteri sadakatini artiran cozumler sunabilirsiniz",
}


def _fallback_template(merchant) -> str:
    """Generate a template-based outreach message when Gemini is unavailable."""
    hook = _CATEGORY_HOOKS.get(
        merchant.category,
        "isletmeniz icin ozel tasarlanmis odeme cozumleriyle buyumenize destek olabilirsiniz"
    )

    rating_mention = ""
    if merchant.rating and merchant.rating >= 4.0:
        rating_mention = (
            f" {merchant.rating} puan ve {merchant.review_count} degerlendirmeyle "
            f"musterilerinizin sizi ne kadar takdir ettigini goruyoruz."
        )
    elif merchant.review_count and merchant.review_count > 100:
        rating_mention = (
            f" {merchant.review_count} musteri degerlendirmesiyle aktif bir isletme "
            f"oldugunuzu goruyoruz."
        )

    return (
        f"Merhaba {merchant.name},\n\n"
        f"Moka United olarak {merchant.district} bolgesindeki isletmenizi inceledik.{rating_mention} "
        f"Moka'nin sunduklariyla {hook}.\n\n"
        f"Hizli kurulum, dusuk komisyon oranlari ve 7/24 destek ekibimizle "
        f"tanismak ister misiniz? Size uygun bir zamanda kisa bir gorusme "
        f"ayarlayalim.\n\n"
        f"Iyi gunler dileriz,\nMoka United Satis Ekibi"
    )
