"""
agent/tools/get_customer_history.py — Fetch cross-channel customer history.

Returns structured history matching the contracts/agent-tools.md CustomerHistory schema.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import customer_repo, ticket_repo

logger = logging.getLogger(__name__)


@dataclass
class TicketSummary:
    ticket_id: str
    channel: str
    status: str
    subject: Optional[str]
    created_at: str
    message_count: int


@dataclass
class CustomerInfo:
    id: str
    display_name: Optional[str]
    company: Optional[str]
    channels_used: list[str]


@dataclass
class CustomerHistoryResult:
    """Result matching contracts/agent-tools.md CustomerHistory schema."""
    customer: Optional[CustomerInfo]
    tickets: list[TicketSummary]
    last_sentiment: Optional[float]
    open_ticket_count: int


async def get_customer_history(
    session: AsyncSession,
    customer_id: uuid.UUID,
    limit: int = 20,
    channel_filter: Optional[str] = None,
    kafka_producer=None,
) -> CustomerHistoryResult:
    """
    Fetch cross-channel interaction history for a customer.

    Returns structured CustomerHistoryResult with:
    - customer: basic customer info
    - tickets: last 20 tickets (most recent first)
    - last_sentiment: sentiment score of most recent inbound message
    - open_ticket_count: number of currently open tickets

    For new customers (not yet in DB): returns empty history (not an error).
    """
    start_time = time.monotonic()

    try:
        # Fetch customer record
        customer = await customer_repo.get_customer_by_id(session, customer_id)

        if not customer:
            logger.debug("Customer %s not found — returning empty history", customer_id)
            return CustomerHistoryResult(
                customer=None,
                tickets=[],
                last_sentiment=None,
                open_ticket_count=0,
            )

        # Fetch tickets
        tickets = await ticket_repo.get_customer_tickets(
            session=session,
            customer_id=customer_id,
            channel_filter=channel_filter,
            limit=limit,
        )

        # Build ticket summaries
        ticket_summaries = []
        open_count = 0
        last_sentiment = None

        for ticket in tickets:
            if ticket.status == "open":
                open_count += 1

            # Build summary (messages may not be loaded — use safe access)
            msg_count = 0
            if hasattr(ticket, "messages") and ticket.messages:
                msg_count = len(ticket.messages)
                # Get sentiment from most recent inbound message
                if last_sentiment is None:
                    inbound_msgs = [
                        m for m in ticket.messages
                        if m.direction == "inbound" and m.sentiment_score is not None
                    ]
                    if inbound_msgs:
                        last_msg = sorted(inbound_msgs, key=lambda m: m.sent_at)[-1]
                        last_sentiment = float(last_msg.sentiment_score)

            ticket_summaries.append(
                TicketSummary(
                    ticket_id=str(ticket.id),
                    channel=ticket.channel,
                    status=ticket.status,
                    subject=ticket.subject,
                    created_at=ticket.created_at.isoformat() if ticket.created_at else None,
                    message_count=msg_count,
                )
            )

        # Collect unique channels used
        channels_used = list({t.channel for t in tickets})

        duration_ms = int((time.monotonic() - start_time) * 1000)

        # Log structured metric
        logger.info(
            '{"timestamp":"%s","ticket_id":null,"tool_name":"get_customer_history",'
            '"input_hash":"%s","output_status":"success","duration_ms":%d,'
            '"channel":null}',
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            str(customer_id)[:16],
            duration_ms,
        )

        return CustomerHistoryResult(
            customer=CustomerInfo(
                id=str(customer.id),
                display_name=customer.display_name,
                company=customer.company,
                channels_used=channels_used,
            ),
            tickets=ticket_summaries,
            last_sentiment=last_sentiment,
            open_ticket_count=open_count,
        )

    except Exception as e:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.error("get_customer_history failed for %s: %s", customer_id, e)
        # E002: return empty on not-found/error — do not raise
        return CustomerHistoryResult(
            customer=None,
            tickets=[],
            last_sentiment=None,
            open_ticket_count=0,
        )
