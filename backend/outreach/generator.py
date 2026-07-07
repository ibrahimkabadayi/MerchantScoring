"""
Moka Fit Score — Outreach Message Generator

Generates personalized outreach messages using Google Gemini API.

TODO: Implement in Phase 7.
"""


async def generate_outreach_message(merchant) -> str:
    """
    Generate a personalized outreach message for the given merchant.
    
    Falls back to a template-based message if Gemini API is unavailable.
    """
    # Fallback template until Gemini integration is implemented
    return (
        f"Merhaba {merchant.name},\n\n"
        f"Moka United olarak, {merchant.category} sektöründeki işletmenizi "
        f"inceledik ve dijital ödeme çözümlerimizin size büyük avantaj "
        f"sağlayacağını düşünüyoruz.\n\n"
        f"Sizinle tanışmak isteriz!"
    )
