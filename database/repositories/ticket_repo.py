"""
database/repositories/ticket_repo.py — Ticket and message CRUD with idempotency.

Key functions:
  - create_ticket_idempotent: 60-second dedup by content_hash + customer_id
  - get_ticket_with_messages: full ticket with message history
  - update_ticket_status: state machine transitions
  - get_customer_tickets: history for a customer
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import IdempotencyKey, Message, Ticket

logger = logging.getLogger(__name__)


def _make_idempotency_key(customer_id: uuid.UUID, content_hash: str) -> str:
    """
    Generate a deterministic idempotency key for ticket creation.
    Key = SHA256(customer_id + ":" + content_hash)
    """
    raw = f"{customer_id}:{content_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def create_ticket_idempotent(
    session: AsyncSession,
    customer_id: uuid.UUID,
    channel: str,
    content_hash: str,
    raw_content: str,
    subject: Optional[str] = None,
    parent_ticket_id: Optional[uuid.UUID] = None,
) -> tuple[uuid.UUID, bool]:
    """
    Create a ticket with 60-second idempotency window.

    If a ticket was created for the same customer + content_hash within
    the last 60 seconds, return the existing ticket_id with duplicate=True.

    Returns:
        (ticket_id, duplicate)
        duplicate=True means an existing ticket was returned
    """
    idem_key = _make_idempotency_key(customer_id, content_hash)
    now = datetime.now(timezone.utc)

    # Check idempotency key
    existing_key = await session.execute(
        select(IdempotencyKey).where(
            IdempotencyKey.key == idem_key,
            IdempotencyKey.expires_at > now,
        )
    )
    key_row = existing_key.scalar_one_or_none()

    if key_row and key_row.result:
        ticket_id = uuid.UUID(key_row.result["ticket_id"])
        logger.debug("Duplicate ticket suppressed via idempotency key: %s", idem_key)
        return ticket_id, True

    # Create new ticket
    ticket_id = uuid.uuid4()
    ticket = Ticket(
        id=ticket_id,
        customer_id=customer_id,
        channel=channel,
        status="open",
        subject=subject or _extract_subject(raw_content),
        parent_ticket_id=parent_ticket_id,
    )
    session.add(ticket)
    await session.flush()

    # Save inbound message
    msg = Message(
        ticket_id=ticket_id,
        direction="inbound",
        channel=channel,
        raw_content=raw_content,
        content_hash=content_hash,
    )
    session.add(msg)

    # Store idempotency key (60-second TTL)
    idem_record = IdempotencyKey(
        key=idem_key,
        result={"ticket_id": str(ticket_id)},
        expires_at=now + timedelta(seconds=60),
    )
    # Use upsert to handle race conditions
    stmt = text("""
        INSERT INTO idempotency_keys (key, result, created_at, expires_at)
        VALUES (:key, :result, :created_at, :expires_at)
        ON CONFLICT (key) DO NOTHING
    """)
    await session.execute(
        stmt,
        {
            "key": idem_key,
            "result": json.dumps({"ticket_id": str(ticket_id)}),
            "created_at": now,
            "expires_at": now + timedelta(seconds=60),
        },
    )

    await session.commit()
    logger.info("Created ticket %s for customer %s", ticket_id, customer_id)
    return ticket_id, False


def _extract_subject(raw_content: str, max_length: int = 100) -> str:
    """Extract a subject line from the first line of message content."""
    first_line = raw_content.split("\n")[0].strip()
    if len(first_line) > max_length:
        return first_line[:max_length - 3] + "..."
    return first_line or "Support Request"


async def get_ticket_with_messages(
    session: AsyncSession, ticket_id: uuid.UUID
) -> Optional[Ticket]:
    """Fetch a ticket with all associated messages, ordered by sent_at."""
    result = await session.execute(
        select(Ticket)
        .options(
            selectinload(Ticket.messages),
            selectinload(Ticket.escalation_record),
        )
        .where(Ticket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def update_ticket_status(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    status: str,
    escalation_reason: Optional[str] = None,
    resolved_by: Optional[str] = None,
) -> bool:
    """
    Update ticket status. Returns True if the ticket was found and updated.
    Valid statuses: open, escalated, pending_human, resolved, closed
    """
    ticket = await session.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket_obj = ticket.scalar_one_or_none()

    if not ticket_obj:
        logger.warning("Ticket not found for status update: %s", ticket_id)
        return False

    ticket_obj.status = status
    if escalation_reason:
        ticket_obj.escalation_reason = escalation_reason
        ticket_obj.escalated = True
    if status == "resolved" and not ticket_obj.resolved_at:
        ticket_obj.resolved_at = datetime.now(timezone.utc)
        ticket_obj.resolved_by = resolved_by or "ai"

    await session.commit()
    return True


async def get_customer_tickets(
    session: AsyncSession,
    customer_id: uuid.UUID,
    channel_filter: Optional[str] = None,
    limit: int = 20,
) -> list[Ticket]:
    """
    Fetch recent tickets for a customer, ordered by most recent first.
    Optionally filter by channel.
    """
    stmt = (
        select(Ticket)
        .where(Ticket.customer_id == customer_id)
        .order_by(Ticket.created_at.desc())
        .limit(limit)
    )

    if channel_filter:
        stmt = stmt.where(Ticket.channel == channel_filter)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def save_outbound_message(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    channel: str,
    content: str,
    content_hash: str,
    sentiment_score: Optional[float] = None,
    agent_decision: Optional[dict] = None,
    delivery_status: str = "sent",
) -> Message:
    """Save an outbound (AI-generated) message to the messages table."""
    msg = Message(
        ticket_id=ticket_id,
        direction="outbound",
        channel=channel,
        raw_content=content,
        content_hash=content_hash,
        sentiment_score=sentiment_score,
        agent_decision=agent_decision,
        delivery_status=delivery_status,
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def check_send_idempotency(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    response_hash: str,
) -> tuple[Optional[int], bool]:
    """
    Check if a response has already been sent for this ticket+hash.
    Returns (message_id, is_duplicate).
    """
    idem_key = hashlib.sha256(
        f"send:{ticket_id}:{response_hash}".encode()
    ).hexdigest()
    now = datetime.now(timezone.utc)

    existing = await session.execute(
        select(IdempotencyKey).where(
            IdempotencyKey.key == idem_key,
            IdempotencyKey.expires_at > now,
        )
    )
    key_row = existing.scalar_one_or_none()

    if key_row and key_row.result:
        return key_row.result.get("message_id"), True

    return None, False


async def save_send_idempotency(
    session: AsyncSession,
    ticket_id: uuid.UUID,
    response_hash: str,
    message_id: int,
    ttl_seconds: int = 3600,
) -> None:
    """Record that a response was sent, preventing duplicates for TTL window."""
    idem_key = hashlib.sha256(
        f"send:{ticket_id}:{response_hash}".encode()
    ).hexdigest()
    now = datetime.now(timezone.utc)

    stmt = text("""
        INSERT INTO idempotency_keys (key, result, created_at, expires_at)
        VALUES (:key, :result, :created_at, :expires_at)
        ON CONFLICT (key) DO NOTHING
    """)
    await session.execute(
        stmt,
        {
            "key": idem_key,
            "result": json.dumps({"message_id": message_id}),
            "created_at": now,
            "expires_at": now + timedelta(seconds=ttl_seconds),
        },
    )
    await session.commit()
