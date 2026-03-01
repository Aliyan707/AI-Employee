"""
api/routers/tickets.py — Ticket management API endpoints.

GET /tickets/{ticket_id}           — full ticket with messages
GET /tickets/{ticket_id}/escalation — escalation record for a ticket
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.ticket_repo import get_ticket_with_messages
from database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class MessageResponse(BaseModel):
    id: int
    direction: str
    channel: str
    raw_content: str
    sentiment_score: Optional[float]
    delivery_status: str
    sent_at: str


class EscalationResponse(BaseModel):
    id: int
    ticket_id: str
    trigger_rule: str
    trigger_detail: Optional[str]
    sentiment_score: Optional[float]
    priority: str
    resolved: bool
    created_at: str


class TicketDetailResponse(BaseModel):
    id: str
    customer_id: str
    channel: str
    status: str
    priority: Optional[str]
    subject: Optional[str]
    escalated: bool
    escalation_reason: Optional[str]
    created_at: str
    resolved_at: Optional[str]
    messages: list[MessageResponse]
    escalation: Optional[EscalationResponse]


# ---------------------------------------------------------------------------
# GET /tickets/{ticket_id}
# ---------------------------------------------------------------------------


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get full ticket details including all messages.

    Returns 404 if ticket not found.
    """
    ticket = await get_ticket_with_messages(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    # Build message responses
    messages = [
        MessageResponse(
            id=msg.id,
            direction=msg.direction,
            channel=msg.channel,
            raw_content=msg.raw_content,
            sentiment_score=float(msg.sentiment_score) if msg.sentiment_score else None,
            delivery_status=msg.delivery_status,
            sent_at=msg.sent_at.isoformat() if msg.sent_at else "",
        )
        for msg in (ticket.messages or [])
    ]

    # Build escalation response
    escalation_resp = None
    if ticket.escalation_record:
        er = ticket.escalation_record
        escalation_resp = EscalationResponse(
            id=er.id,
            ticket_id=str(er.ticket_id),
            trigger_rule=er.trigger_rule,
            trigger_detail=er.trigger_detail,
            sentiment_score=float(er.sentiment_score) if er.sentiment_score else None,
            priority=er.priority,
            resolved=er.resolved,
            created_at=er.created_at.isoformat() if er.created_at else "",
        )

    return TicketDetailResponse(
        id=str(ticket.id),
        customer_id=str(ticket.customer_id),
        channel=ticket.channel,
        status=ticket.status,
        priority=ticket.priority,
        subject=ticket.subject,
        escalated=ticket.escalated,
        escalation_reason=ticket.escalation_reason,
        created_at=ticket.created_at.isoformat() if ticket.created_at else "",
        resolved_at=ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        messages=messages,
        escalation=escalation_resp,
    )


# ---------------------------------------------------------------------------
# GET /tickets/{ticket_id}/escalation
# ---------------------------------------------------------------------------


@router.get("/{ticket_id}/escalation", response_model=EscalationResponse)
async def get_ticket_escalation(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get escalation record for a specific ticket.

    Returns 404 if ticket not found or not escalated.
    """
    ticket = await get_ticket_with_messages(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    if not ticket.escalation_record:
        raise HTTPException(
            status_code=404,
            detail=f"Ticket {ticket_id} has no escalation record",
        )

    er = ticket.escalation_record
    return EscalationResponse(
        id=er.id,
        ticket_id=str(er.ticket_id),
        trigger_rule=er.trigger_rule,
        trigger_detail=er.trigger_detail,
        sentiment_score=float(er.sentiment_score) if er.sentiment_score else None,
        priority=er.priority,
        resolved=er.resolved,
        created_at=er.created_at.isoformat() if er.created_at else "",
    )
