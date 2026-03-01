"""
channels/whatsapp/webhook.py — Twilio WhatsApp webhook handler.

Validates HMAC-SHA1 Twilio signature and normalises payload to IntakeEvent.
"""

import base64
import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel

from channels.webform.handler import (
    ChannelMetadata,
    IntakeEvent,
    compute_content_hash,
)
from database.repositories.customer_repo import normalise_phone

logger = logging.getLogger(__name__)


class TwilioWebhookPayload(BaseModel):
    """
    Pydantic model for Twilio WhatsApp webhook POST body.
    Twilio sends form-encoded data.
    """
    From: str           # e.g. "whatsapp:+14155552671"
    To: str             # e.g. "whatsapp:+14155238886"
    Body: str           # Message text content
    MessageSid: str     # Twilio message identifier


def validate_twilio_signature(
    auth_token: str,
    signature: str,
    url: str,
    params: dict,
) -> bool:
    """
    Validate Twilio HMAC-SHA1 webhook signature.

    Twilio's validation algorithm:
    1. Take the full URL of the request including any query parameters
    2. If POST: sort POST params alphabetically, append each key+value to URL
    3. Sign the resulting string with HMAC-SHA1 using the auth token
    4. Base64-encode the result
    5. Compare with X-Twilio-Signature header

    Returns True if signature is valid, False otherwise.
    """
    if not auth_token or not signature:
        return False

    # Sort params alphabetically and append to URL
    sorted_params = sorted(params.items())
    param_string = "".join(f"{k}{v}" for k, v in sorted_params)
    computed_str = url + param_string

    # HMAC-SHA1
    mac = hmac.new(
        auth_token.encode("utf-8"),
        msg=computed_str.encode("utf-8"),
        digestmod=hashlib.sha1,
    )
    expected = base64.b64encode(mac.digest()).decode("utf-8")

    return hmac.compare_digest(expected, signature)


def normalise_whatsapp(payload: TwilioWebhookPayload) -> IntakeEvent:
    """
    Convert a Twilio WhatsApp payload into a normalised IntakeEvent.

    Extracts phone number from "whatsapp:+E164" format.
    Sets channel="whatsapp".
    """
    # Extract phone: "whatsapp:+14155552671" → "+14155552671"
    raw_phone = payload.From
    if raw_phone.startswith("whatsapp:"):
        raw_phone = raw_phone[len("whatsapp:"):]

    # Normalise to E.164
    phone = normalise_phone(raw_phone) or raw_phone

    raw_content = payload.Body.strip()
    content_hash = compute_content_hash(raw_content)

    return IntakeEvent(
        schema_version="1.0",
        event_type="customer_inquiry",
        event_id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        session_id=str(uuid.uuid4()),
        channel="whatsapp",
        raw_content=raw_content,
        content_hash=content_hash,
        customer_identifiers={"phone": phone, "whatsapp_id": phone},
        customer_name=None,
        channel_metadata=ChannelMetadata(
            message_sid=payload.MessageSid,
        ),
    )
