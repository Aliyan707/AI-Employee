"""
agent/tools/create_ticket.py — Tool wrapper for ticket creation with idempotency.

Calls ticket_repo.create_ticket_idempotent and emits a metric event.
"""

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import ticket_repo

logger = logging.getLogger(__name__)


class CreateTicketInput(BaseModel):
    """Input schema for create_ticket tool."""
    customer_id: uuid.UUID
    channel: str                        # email | whatsapp | webform
    raw_content: str
    content_hash: str                   # SHA-256 of raw_content
    subject: Optional[str] = None
    parent_ticket_id: Optional[uuid.UUID] = None


@dataclass
class ToolResult:
    """Result of create_ticket tool call."""
    ticket_id: uuid.UUID
    status: str
    created: bool
    duplicate: bool


async def create_ticket(
    session: AsyncSession,
    input_data: CreateTicketInput,
    kafka_producer=None,
) -> ToolResult:
    """
    Create a support ticket with idempotency protection.

    - If same customer + content_hash within 60s: returns existing ticket (duplicate=True)
    - Otherwise: creates new ticket, inbound message, and idempotency key

    Also emits an agent_metrics event to Kafka (if producer available).
    """
    start_time = time.monotonic()

    try:
        ticket_id, duplicate = await ticket_repo.create_ticket_idempotent(
            session=session,
            customer_id=input_data.customer_id,
            channel=input_data.channel,
            content_hash=input_data.content_hash,
            raw_content=input_data.raw_content,
            subject=input_data.subject,
            parent_ticket_id=input_data.parent_ticket_id,
        )

        duration_ms = int((time.monotonic() - start_time) * 1000)
        status = "duplicate" if duplicate else "open"

        # Emit metric event
        await _emit_metric(
            kafka_producer=kafka_producer,
            tool_name="create_ticket",
            ticket_id=ticket_id,
            channel=input_data.channel,
            input_hash=input_data.content_hash[:16],
            output_status="success",
            duration_ms=duration_ms,
        )

        logger.info(
            '{"timestamp":"%s","ticket_id":"%s","tool_name":"create_ticket",'
            '"input_hash":"%s","output_status":"success","duration_ms":%d,'
            '"channel":"%s","duplicate":%s}',
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ticket_id,
            input_data.content_hash[:16],
            duration_ms,
            input_data.channel,
            str(duplicate).lower(),
        )

        return ToolResult(
            ticket_id=ticket_id,
            status=status,
            created=not duplicate,
            duplicate=duplicate,
        )

    except Exception as e:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        await _emit_metric(
            kafka_producer=kafka_producer,
            tool_name="create_ticket",
            ticket_id=None,
            channel=input_data.channel,
            input_hash=input_data.content_hash[:16],
            output_status="E001",
            duration_ms=duration_ms,
            error_code="E001",
        )
        logger.error("create_ticket failed: %s", e)
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
    """Publish a tool execution metric to the cs.metrics Kafka topic."""
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
        logger.warning("Failed to emit metric to Kafka: %s", e)
