"""
agent/tools/send_response.py — Send formatted response with idempotency.

Checks for duplicate sends (ticket_id + response_hash), saves outbound message,
and returns SendResult with sent/duplicate status.
"""

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ticket_repo

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    """Result of send_response tool call."""
    message_id: Optional[int]
    ticket_id: str
    channel: str
    sent: bool
    duplicate: bool
    sent_at: Optional[str] = None


def compute_response_hash(text: str) -> str:
    """Compute SHA-256 hash of response text for idempotency."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def send_response(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    channel: str,
    response_text: str,
    response_hash: str,
    metadata: Optional[dict] = None,
    kafka_producer=None,
) -> SendResult:
    """
    Send a formatted response and save it to the messages table.

    Idempotency: checks SHA256(ticket_id + response_hash) before sending.
    If duplicate found within TTL window: returns SendResult(sent=False, duplicate=True).

    Steps:
    1. Check idempotency key
    2. Save outbound Message row in DB
    3. Store idempotency key
    4. Update ticket status to resolved
    5. Emit metric event

    Args:
        session: async database session
        ticket_id: UUID of the ticket to respond to
        channel: "email" | "whatsapp" | "webform"
        response_text: already-formatted response text
        response_hash: SHA-256 of response_text
        metadata: optional dict with kb_article_ids, sentiment_score, etc.
        kafka_producer: Kafka producer for cs.metrics events

    Returns:
        SendResult with message_id, sent, and duplicate flags
    """
    start_time = time.monotonic()

    try:
        # Step 1: Check idempotency
        existing_msg_id, is_duplicate = await ticket_repo.check_send_idempotency(
            session=session,
            ticket_id=ticket_id,
            response_hash=response_hash,
        )

        if is_duplicate:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(
                '{"timestamp":"%s","ticket_id":"%s","tool_name":"send_response",'
                '"output_status":"duplicate","duration_ms":%d,"channel":"%s"}',
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                str(ticket_id),
                duration_ms,
                channel,
            )
            return SendResult(
                message_id=existing_msg_id,
                ticket_id=str(ticket_id),
                channel=channel,
                sent=False,
                duplicate=True,
            )

        # Step 2: Save outbound message
        sentiment_score = None
        kb_article_ids = None
        agent_decision = metadata or {}

        if metadata:
            sentiment_score = metadata.get("sentiment_score")
            kb_article_ids = metadata.get("kb_article_ids")

        msg = await ticket_repo.save_outbound_message(
            session=session,
            ticket_id=ticket_id,
            channel=channel,
            content=response_text,
            content_hash=response_hash,
            sentiment_score=float(sentiment_score) if sentiment_score is not None else None,
            agent_decision=agent_decision,
            delivery_status="sent",
        )

        # Update KB article IDs on ticket if provided
        if kb_article_ids:
            from sqlalchemy import select
            from database.models import Ticket
            result = await session.execute(
                select(Ticket).where(Ticket.id == ticket_id)
            )
            ticket = result.scalar_one_or_none()
            if ticket:
                ticket.kb_article_ids = [uuid.UUID(str(aid)) for aid in kb_article_ids]
                await session.commit()

        # Step 3: Store idempotency key
        await ticket_repo.save_send_idempotency(
            session=session,
            ticket_id=ticket_id,
            response_hash=response_hash,
            message_id=msg.id,
            ttl_seconds=3600,
        )

        # Step 4: Update ticket status to resolved
        is_escalation = agent_decision.get("is_escalation_holding_message", False)
        if not is_escalation:
            await ticket_repo.update_ticket_status(
                session=session,
                ticket_id=ticket_id,
                status="resolved",
                resolved_by="ai",
            )

        sent_at = msg.sent_at.isoformat() if msg.sent_at else datetime.now(timezone.utc).isoformat()
        duration_ms = int((time.monotonic() - start_time) * 1000)

        # Step 5: Emit metric
        logger.info(
            '{"timestamp":"%s","ticket_id":"%s","tool_name":"send_response",'
            '"input_hash":"%s","output_status":"success","duration_ms":%d,"channel":"%s"}',
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            str(ticket_id),
            response_hash[:16],
            duration_ms,
            channel,
        )

        await _emit_metric(
            kafka_producer=kafka_producer,
            tool_name="send_response",
            ticket_id=ticket_id,
            channel=channel,
            input_hash=response_hash[:16],
            output_status="success",
            duration_ms=duration_ms,
        )

        return SendResult(
            message_id=msg.id,
            ticket_id=str(ticket_id),
            channel=channel,
            sent=True,
            duplicate=False,
            sent_at=sent_at,
        )

    except Exception as e:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("send_response failed for ticket %s: %s", ticket_id, e)
        await _emit_metric(
            kafka_producer=kafka_producer,
            tool_name="send_response",
            ticket_id=ticket_id,
            channel=channel,
            input_hash=response_hash[:16] if response_hash else "",
            output_status="E001",
            duration_ms=duration_ms,
            error_code="E001",
        )
        raise


async def _emit_metric(
    kafka_producer,
    tool_name: str,
    ticket_id: Optional[uuid.UUID],
    channel: Optional[str],
    input_hash: str,
    output_status: str,
    duration_ms: int,
    error_code: Optional[str] = None,
) -> None:
    """Publish metric event to cs.metrics Kafka topic."""
    if not kafka_producer:
        return

    metric_event = {
        "tool_name": tool_name,
        "ticket_id": str(ticket_id) if ticket_id else None,
        "channel": channel,
        "input_hash": input_hash,
        "output_status": output_status,
        "duration_ms": duration_ms,
        "error_code": error_code,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    try:
        await kafka_producer.send(
            "cs.metrics",
            value=json.dumps(metric_event).encode("utf-8"),
        )
    except Exception as e:
        logger.warning("Failed to emit send_response metric: %s", e)
