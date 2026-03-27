"""
agent/tools/escalate_to_human.py — Escalation tool with idempotency.

Idempotent: one escalation record per ticket.
Updates ticket status to "escalated", inserts EscalationRecord,
POSTs to ESCALATION_QUEUE_WEBHOOK, and returns channel-appropriate holding message.
"""

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database.models import EscalationRecord, Ticket
from database.repositories import ticket_repo

logger = logging.getLogger(__name__)
settings = get_settings()

# Channel-appropriate holding messages (within character limits)
HOLDING_MESSAGES = {
    "whatsapp": "Your request needs specialist attention. We've connected you with our team and will follow up shortly. Reference: #{ticket_id}",
    "email": (
        "Thank you for reaching out. Your inquiry requires specialist attention and has been escalated to our support team.\n\n"
        "A team member will contact you within 2 business hours.\n\n"
        "Your support reference: #{ticket_id}"
    ),
    "webform": (
        "Your inquiry has been escalated to our support specialists.\n\n"
        "A team member will contact you within 2 business hours.\n\n"
        "Reference: #{ticket_id}"
    ),
}


@dataclass
class EscalationResult:
    """Result of escalate_to_human tool call."""
    escalation_id: Optional[int]
    ticket_id: str
    status: str                    # "escalated" | "already_escalated"
    queue_position: Optional[int]
    customer_message: Optional[str]
    already_escalated: bool


async def escalate_to_human(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    trigger_rule: str,
    trigger_detail: str,
    sentiment_score: Optional[float],
    priority: str,
    channel: str,
    conversation_context: str = "",
    kafka_producer=None,
) -> EscalationResult:
    """
    Escalate a ticket to the human agent queue.

    Idempotency: checks for existing EscalationRecord before inserting.
    If already escalated: returns EscalationResult(status="already_escalated").

    Steps:
    1. Check idempotency (existing escalation_records row)
    2. Insert EscalationRecord
    3. Update ticket status to "escalated"
    4. POST to ESCALATION_QUEUE_WEBHOOK
    5. Publish to cs.escalation Kafka topic
    6. Return holding message for the channel

    Args:
        session: async database session
        ticket_id: UUID of the ticket to escalate
        trigger_rule: why escalation was triggered (pricing/refund/legal/etc.)
        trigger_detail: specific text or detail that triggered escalation
        sentiment_score: sentiment score at time of escalation
        priority: P1 | P2 | P3
        channel: channel for holding message formatting
        conversation_context: full conversation summary for human agent
        kafka_producer: Kafka producer for cs.escalation events

    Returns:
        EscalationResult with escalation_id, status, and customer_message
    """
    start_time = time.monotonic()

    try:
        # Step 1: Idempotency check
        existing = await session.execute(
            select(EscalationRecord).where(EscalationRecord.ticket_id == ticket_id)
        )
        existing_record = existing.scalar_one_or_none()

        if existing_record:
            logger.info(
                "Ticket %s already escalated (escalation_id=%s)",
                ticket_id,
                existing_record.id,
            )
            return EscalationResult(
                escalation_id=existing_record.id,
                ticket_id=str(ticket_id),
                status="already_escalated",
                queue_position=None,
                customer_message=None,
                already_escalated=True,
            )

        # Step 2: Insert EscalationRecord
        escalation = EscalationRecord(
            ticket_id=ticket_id,
            trigger_rule=trigger_rule,
            trigger_detail=trigger_detail,
            sentiment_score=float(sentiment_score) if sentiment_score is not None else None,
            priority=priority,
        )
        session.add(escalation)
        await session.flush()

        # Step 3: Update ticket status
        await ticket_repo.update_ticket_status(
            session=session,
            ticket_id=ticket_id,
            status="escalated",
            escalation_reason=trigger_detail,
        )

        await session.commit()
        await session.refresh(escalation)

        escalation_id = escalation.id

        # Step 4: POST to escalation webhook
        queue_position = await _notify_escalation_webhook(
            ticket_id=ticket_id,
            escalation_id=escalation_id,
            trigger_rule=trigger_rule,
            trigger_detail=trigger_detail,
            sentiment_score=sentiment_score,
            priority=priority,
            channel=channel,
            conversation_context=conversation_context,
        )

        # Step 5: Publish to Kafka cs.escalation topic
        if kafka_producer:
            await _publish_escalation_event(
                kafka_producer=kafka_producer,
                ticket_id=ticket_id,
                escalation_id=escalation_id,
                trigger_rule=trigger_rule,
                priority=priority,
                channel=channel,
            )

        # Step 6: Build channel-appropriate holding message
        customer_message = _build_holding_message(channel, ticket_id)

        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            '{"timestamp":"%s","ticket_id":"%s","tool_name":"escalate_to_human",'
            '"output_status":"success","duration_ms":%d,"channel":"%s",'
            '"trigger_rule":"%s","priority":"%s"}',
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            str(ticket_id),
            duration_ms,
            channel,
            trigger_rule,
            priority,
        )

        return EscalationResult(
            escalation_id=escalation_id,
            ticket_id=str(ticket_id),
            status="escalated",
            queue_position=queue_position,
            customer_message=customer_message,
            already_escalated=False,
        )

    except Exception as e:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("escalate_to_human failed for ticket %s: %s", ticket_id, e)
        raise


def _build_holding_message(channel: str, ticket_id: uuid.UUID) -> str:
    """Build a channel-appropriate holding message."""
    template = HOLDING_MESSAGES.get(channel, HOLDING_MESSAGES["webform"])
    message = template.replace("#{ticket_id}", str(ticket_id)[:8].upper())

    # Enforce WhatsApp character limit
    if channel == "whatsapp" and len(message) > 300:
        message = f"Connecting you with our team. Ref: #{str(ticket_id)[:8].upper()}"

    return message


async def _notify_escalation_webhook(
    ticket_id: uuid.UUID,
    escalation_id: int,
    trigger_rule: str,
    trigger_detail: str,
    sentiment_score: Optional[float],
    priority: str,
    channel: str,
    conversation_context: str,
) -> Optional[int]:
    """POST escalation notification to the configured webhook URL."""
    webhook_url = settings.escalation_queue_webhook
    if not webhook_url:
        logger.debug("No ESCALATION_QUEUE_WEBHOOK configured — skipping webhook")
        return None

    payload = {
        "ticket_id": str(ticket_id),
        "escalation_id": escalation_id,
        "trigger_rule": trigger_rule,
        "trigger_detail": trigger_detail,
        "sentiment_score": sentiment_score,
        "priority": priority,
        "channel": channel,
        "conversation_context": conversation_context,
        "escalated_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            # Try to get queue position from response
            try:
                data = response.json()
                return data.get("queue_position")
            except Exception:
                return None
    except Exception as e:
        logger.warning("Escalation webhook POST failed: %s", e)
        return None


async def _publish_escalation_event(
    kafka_producer,
    ticket_id: uuid.UUID,
    escalation_id: int,
    trigger_rule: str,
    priority: str,
    channel: str,
) -> None:
    """Publish escalation event to cs.escalation Kafka topic."""
    event = {
        "ticket_id": str(ticket_id),
        "escalation_id": escalation_id,
        "trigger_rule": trigger_rule,
        "priority": priority,
        "channel": channel,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        await kafka_producer.send(
            "cs.escalation",
            value=json.dumps(event).encode("utf-8"),
        )
    except Exception as e:
        logger.warning("Failed to publish escalation event to Kafka: %s", e)
