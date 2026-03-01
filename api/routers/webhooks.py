"""
api/routers/webhooks.py — Webhook endpoints for all three channels.

POST /webhooks/webform  — Web form submission
POST /webhooks/whatsapp — Twilio WhatsApp webhook
POST /webhooks/gmail    — Gmail PubSub push notification
POST /webhooks/simulate — Debug endpoint (development only)
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from agent.orchestrator import OrchestratorAgent
from channels.webform.handler import WebformPayload, normalise_webform
from config import get_settings
from database.repositories.customer_repo import resolve_or_create_customer
from database.session import get_db

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()
orchestrator = OrchestratorAgent()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class WebhookResponse(BaseModel):
    response_text: Optional[str]
    ticket_id: Optional[str]
    channel: str
    escalated: bool


class AsyncWebhookResponse(BaseModel):
    accepted: bool
    idempotency_key: str
    message: str = "Request accepted and queued for processing"


# ---------------------------------------------------------------------------
# POST /webhooks/webform
# ---------------------------------------------------------------------------


@router.post("/webform", response_model=WebhookResponse)
async def webhook_webform(
    payload: WebformPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Process a web form submission through the full 7-step pipeline.

    In prototype mode (pre-Kafka): runs pipeline synchronously and returns response.
    After Kafka integration: publishes to cs.intake and returns 202.
    """
    logger.info("Received webform submission from email: ***@***.***")

    # Normalise to IntakeEvent
    intake_event = normalise_webform(payload)

    # Resolve customer identity
    customer_id, was_created = await resolve_or_create_customer(
        session=db,
        identifiers=intake_event.customer_identifiers,
        display_name=intake_event.customer_name,
    )
    intake_event.customer_id = customer_id

    # Run pipeline (prototype mode: direct call)
    try:
        kafka_producer = await _get_kafka_producer_optional()
    except Exception:
        kafka_producer = None

    result = await orchestrator.run(
        session=db,
        intake_event=intake_event,
        kafka_producer=kafka_producer,
    )

    return WebhookResponse(
        response_text=result.response_text,
        ticket_id=str(result.ticket_id) if result.ticket_id else None,
        channel=result.channel,
        escalated=result.escalated,
    )


# ---------------------------------------------------------------------------
# POST /webhooks/whatsapp
# ---------------------------------------------------------------------------


@router.post("/whatsapp")
async def webhook_whatsapp(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Process a Twilio WhatsApp webhook.

    Validates HMAC-SHA1 signature, normalises payload, runs pipeline,
    and sends response via Twilio.
    """
    from channels.whatsapp.webhook import (
        TwilioWebhookPayload,
        normalise_whatsapp,
        validate_twilio_signature,
    )
    from channels.whatsapp.sender import send_whatsapp

    # Parse form data (Twilio sends form-encoded)
    form_data = await request.form()
    body_bytes = await request.body()

    # Validate Twilio signature
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form_dict = dict(form_data)

    if settings.twilio_auth_token and not settings.is_development:
        is_valid = validate_twilio_signature(
            auth_token=settings.twilio_auth_token,
            signature=signature,
            url=url,
            params=form_dict,
        )
        if not is_valid:
            logger.warning("Invalid Twilio signature from %s", request.client.host if request.client else "unknown")
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    # Parse payload
    try:
        twilio_payload = TwilioWebhookPayload(
            From=form_dict.get("From", ""),
            To=form_dict.get("To", ""),
            Body=form_dict.get("Body", ""),
            MessageSid=form_dict.get("MessageSid", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    if not twilio_payload.Body:
        # Empty message — return empty TwiML response
        return Response(
            content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
            media_type="text/xml",
        )

    # Normalise to IntakeEvent
    intake_event = normalise_whatsapp(twilio_payload)

    # Resolve customer
    customer_id, _ = await resolve_or_create_customer(
        session=db,
        identifiers=intake_event.customer_identifiers,
        display_name=intake_event.customer_name,
    )
    intake_event.customer_id = customer_id

    # Run pipeline
    kafka_producer = await _get_kafka_producer_optional()
    result = await orchestrator.run(session=db, intake_event=intake_event, kafka_producer=kafka_producer)

    # Send via Twilio
    if result.response_text and intake_event.channel_metadata.message_sid:
        phone = twilio_payload.From
        await send_whatsapp(to_number=phone, text=result.response_text)

    # Return Twilio-compatible XML response
    twiml_body = ""
    if result.response_text:
        from xml.sax.saxutils import escape
        twiml_body = f"<Message>{escape(result.response_text)}</Message>"

    return Response(
        content=f"<?xml version='1.0' encoding='UTF-8'?><Response>{twiml_body}</Response>",
        media_type="text/xml",
    )


# ---------------------------------------------------------------------------
# POST /webhooks/gmail
# ---------------------------------------------------------------------------


@router.post("/gmail")
async def webhook_gmail(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Process a Gmail PubSub push notification.

    Decodes the base64 PubSub message, fetches full Gmail message,
    runs pipeline, and sends reply in same thread.
    """
    from channels.gmail.reader import decode_gmail_push
    from channels.gmail.sender import send_gmail_reply

    # Parse PubSub push
    body = await request.json()
    pubsub_message = body.get("message", {})
    pubsub_data = pubsub_message.get("data", "")

    if not pubsub_data:
        logger.warning("Gmail webhook received empty PubSub data")
        return {"status": "ok"}  # Return 200 to avoid PubSub retries

    try:
        intake_event = await decode_gmail_push(pubsub_data)
    except Exception as e:
        logger.error("Failed to decode Gmail push: %s", e)
        return {"status": "error", "detail": str(e)}

    # Resolve customer
    customer_id, _ = await resolve_or_create_customer(
        session=db,
        identifiers=intake_event.customer_identifiers,
        display_name=intake_event.customer_name,
    )
    intake_event.customer_id = customer_id

    # Run pipeline
    kafka_producer = await _get_kafka_producer_optional()
    result = await orchestrator.run(session=db, intake_event=intake_event, kafka_producer=kafka_producer)

    # Send Gmail reply
    if result.response_text and intake_event.channel_metadata.thread_id:
        to_address = intake_event.customer_identifiers.get("email", "")
        subject = intake_event.channel_metadata.subject or "Re: Support Request"
        if not subject.startswith("Re:"):
            subject = f"Re: {subject}"

        # Format as HTML for Gmail
        html_body = result.response_text.replace("\n", "<br>")

        await send_gmail_reply(
            thread_id=intake_event.channel_metadata.thread_id,
            to_address=to_address,
            subject=subject,
            html_body=html_body,
        )

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /webhooks/simulate (development only)
# ---------------------------------------------------------------------------


class SimulatePayload(BaseModel):
    channel: str
    raw_content: str
    customer_identifiers: dict
    customer_name: Optional[str] = None
    subject: Optional[str] = None


@router.post("/simulate", response_model=WebhookResponse)
async def webhook_simulate(
    payload: SimulatePayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Debug endpoint for testing pipeline without real channel credentials.
    Only available in development environment.

    Accepts a normalised IntakeEvent-like payload and runs the full pipeline.
    """
    if not settings.is_development:
        raise HTTPException(
            status_code=403,
            detail="Simulation endpoint only available in development environment",
        )

    # Build IntakeEvent directly
    from channels.webform.handler import ChannelMetadata, IntakeEvent, compute_content_hash
    import uuid
    from datetime import datetime, timezone

    content_hash = compute_content_hash(payload.raw_content)

    intake_event = IntakeEvent(
        schema_version="1.0",
        event_type="customer_inquiry",
        event_id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        session_id=str(uuid.uuid4()),
        channel=payload.channel,
        raw_content=payload.raw_content,
        content_hash=content_hash,
        customer_identifiers=payload.customer_identifiers,
        customer_name=payload.customer_name,
        channel_metadata=ChannelMetadata(subject=payload.subject),
    )

    # Resolve customer
    customer_id, _ = await resolve_or_create_customer(
        session=db,
        identifiers=payload.customer_identifiers,
        display_name=payload.customer_name,
    )
    intake_event.customer_id = customer_id

    result = await orchestrator.run(session=db, intake_event=intake_event)

    return WebhookResponse(
        response_text=result.response_text,
        ticket_id=str(result.ticket_id) if result.ticket_id else None,
        channel=result.channel,
        escalated=result.escalated,
    )


# ---------------------------------------------------------------------------
# Helper: optional Kafka producer
# ---------------------------------------------------------------------------


async def _get_kafka_producer_optional():
    """Try to get Kafka producer; return None if Kafka is unavailable."""
    try:
        from workers.kafka_client import get_kafka_producer
        return await get_kafka_producer()
    except Exception:
        return None
