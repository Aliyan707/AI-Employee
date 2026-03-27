"""
channels/whatsapp/sender.py — Send WhatsApp messages via Twilio REST API.

send_whatsapp(to_number, text) -> bool
  - Asserts len(text) <= 300 before sending
  - Returns False (does not raise) on Twilio API errors
"""

import logging
from typing import Optional

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

WHATSAPP_MAX_CHARS = 300


async def send_whatsapp(to_number: str, text: str) -> bool:
    """
    Send a WhatsApp message via Twilio REST API.

    Args:
        to_number: recipient phone number in E.164 format or "whatsapp:+E164"
        text: message text (must be <= 300 characters)

    Returns:
        True on success, False on any error (does not raise)
    """
    # Enforce character limit
    if len(text) > WHATSAPP_MAX_CHARS:
        logger.error(
            "WhatsApp message exceeds %d chars (%d) — truncating",
            WHATSAPP_MAX_CHARS,
            len(text),
        )
        text = text[:WHATSAPP_MAX_CHARS - 3] + "..."

    # Ensure "whatsapp:" prefix for Twilio
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    from_number = settings.twilio_whatsapp_from
    if not from_number.startswith("whatsapp:"):
        from_number = f"whatsapp:{from_number}"

    # Check configuration
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        logger.warning(
            "Twilio credentials not configured — WhatsApp message not sent to %s",
            to_number[:8] + "***",
        )
        return False

    try:
        from twilio.rest import Client

        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

        message = client.messages.create(
            from_=from_number,
            to=to_number,
            body=text,
        )

        logger.info(
            "WhatsApp message sent: sid=%s, to=%s***",
            message.sid,
            to_number[:8],
        )
        return True

    except Exception as e:
        logger.error("Twilio send_whatsapp failed: %s", e)
        return False
