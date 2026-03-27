"""
api/routers/customers.py — Customer history API endpoints.

GET /customers/{customer_id}/history — cross-channel ticket history
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.customer_repo import get_customer_by_id
from database.repositories.ticket_repo import get_customer_tickets
from database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class TicketSummaryResponse(BaseModel):
    ticket_id: str
    channel: str
    status: str
    subject: Optional[str]
    escalated: bool
    created_at: str
    resolved_at: Optional[str]


class CustomerHistoryResponse(BaseModel):
    customer_id: str
    display_name: Optional[str]
    company: Optional[str]
    primary_email: Optional[str]
    tickets: list[TicketSummaryResponse]
    total_count: int
    open_count: int


@router.get("/{customer_id}/history", response_model=CustomerHistoryResponse)
async def get_customer_history(
    customer_id: uuid.UUID,
    channel: Optional[str] = Query(None, description="Filter by channel: email|whatsapp|webform"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of tickets to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cross-channel ticket history for a customer.

    Supports optional ?channel filter and ?limit pagination.
    Returns 404 if customer not found.
    """
    # Validate channel filter
    if channel and channel not in ("email", "whatsapp", "webform"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid channel '{channel}'. Must be: email, whatsapp, or webform",
        )

    customer = await get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    tickets = await get_customer_tickets(
        session=db,
        customer_id=customer_id,
        channel_filter=channel,
        limit=limit,
    )

    open_count = sum(1 for t in tickets if t.status == "open")

    ticket_summaries = [
        TicketSummaryResponse(
            ticket_id=str(t.id),
            channel=t.channel,
            status=t.status,
            subject=t.subject,
            escalated=t.escalated,
            created_at=t.created_at.isoformat() if t.created_at else "",
            resolved_at=t.resolved_at.isoformat() if t.resolved_at else None,
        )
        for t in tickets
    ]

    return CustomerHistoryResponse(
        customer_id=str(customer.id),
        display_name=customer.display_name,
        company=customer.company,
        primary_email=customer.primary_email,
        tickets=ticket_summaries,
        total_count=len(ticket_summaries),
        open_count=open_count,
    )
