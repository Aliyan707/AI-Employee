"""
database/repositories/metrics_repo.py — Agent metrics and daily report aggregation.
"""

import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import AgentMetric, DailyReport, Ticket

logger = logging.getLogger(__name__)


async def insert_metric(
    session: AsyncSession,
    tool_name: str,
    output_status: str,
    duration_ms: int,
    ticket_id: Optional[uuid.UUID] = None,
    channel: Optional[str] = None,
    input_hash: Optional[str] = None,
    error_code: Optional[str] = None,
) -> AgentMetric:
    """Insert a single tool execution metric."""
    metric = AgentMetric(
        ticket_id=ticket_id,
        tool_name=tool_name,
        channel=channel,
        input_hash=input_hash,
        output_status=output_status,
        duration_ms=duration_ms,
        error_code=error_code,
    )
    session.add(metric)
    await session.commit()
    await session.refresh(metric)
    return metric


async def get_daily_summary(
    session: AsyncSession,
    report_date: date,
) -> dict:
    """
    Aggregate ticket counts, mean sentiment, and escalation rate for a date.

    Returns a dict matching the DailyReport schema:
    {
        "total_tickets": int,
        "tickets_by_channel": {"email": N, "whatsapp": N, "webform": N},
        "mean_sentiment": float | None,
        "escalation_count": int,
        "escalation_rate": float,
        "top_topics": [{"topic": str, "count": int}]
    }
    """
    # Total tickets and channel breakdown
    channel_result = await session.execute(
        text("""
            SELECT
                channel,
                COUNT(*) as count
            FROM tickets
            WHERE DATE(created_at) = :report_date
            GROUP BY channel
        """),
        {"report_date": report_date},
    )
    channel_rows = channel_result.fetchall()

    tickets_by_channel = {"email": 0, "whatsapp": 0, "webform": 0}
    total_tickets = 0
    for row in channel_rows:
        ch = row[0]
        count = row[1]
        if ch in tickets_by_channel:
            tickets_by_channel[ch] = count
        total_tickets += count

    # Mean sentiment from messages
    sentiment_result = await session.execute(
        text("""
            SELECT AVG(m.sentiment_score)
            FROM messages m
            JOIN tickets t ON m.ticket_id = t.id
            WHERE DATE(t.created_at) = :report_date
              AND m.sentiment_score IS NOT NULL
              AND m.direction = 'inbound'
        """),
        {"report_date": report_date},
    )
    mean_sentiment_raw = sentiment_result.scalar()
    mean_sentiment = float(mean_sentiment_raw) if mean_sentiment_raw else None

    # Escalation count
    escalation_result = await session.execute(
        text("""
            SELECT COUNT(*)
            FROM tickets
            WHERE DATE(created_at) = :report_date
              AND escalated = TRUE
        """),
        {"report_date": report_date},
    )
    escalation_count = escalation_result.scalar() or 0

    # Escalation rate
    escalation_rate = 0.0
    if total_tickets > 0:
        escalation_rate = round((escalation_count / total_tickets) * 100, 2)

    # Top topics (extracted from ticket subjects)
    topics_result = await session.execute(
        text("""
            SELECT subject, COUNT(*) as count
            FROM tickets
            WHERE DATE(created_at) = :report_date
              AND subject IS NOT NULL
            GROUP BY subject
            ORDER BY count DESC
            LIMIT 5
        """),
        {"report_date": report_date},
    )
    top_topics = [
        {"topic": row[0], "count": row[1]}
        for row in topics_result.fetchall()
    ]

    return {
        "total_tickets": total_tickets,
        "tickets_by_channel": tickets_by_channel,
        "mean_sentiment": mean_sentiment,
        "escalation_count": escalation_count,
        "escalation_rate": escalation_rate,
        "top_topics": top_topics,
    }


async def upsert_daily_report(
    session: AsyncSession,
    report_date: date,
    summary: dict,
) -> DailyReport:
    """Upsert a daily report row."""
    stmt = text("""
        INSERT INTO daily_reports (
            id, report_date, total_tickets, tickets_by_channel,
            top_topics, mean_sentiment, escalation_count, escalation_rate, generated_at
        )
        VALUES (
            gen_random_uuid(), :report_date, :total_tickets, :tickets_by_channel::jsonb,
            :top_topics::jsonb, :mean_sentiment, :escalation_count, :escalation_rate, NOW()
        )
        ON CONFLICT (report_date) DO UPDATE SET
            total_tickets = EXCLUDED.total_tickets,
            tickets_by_channel = EXCLUDED.tickets_by_channel,
            top_topics = EXCLUDED.top_topics,
            mean_sentiment = EXCLUDED.mean_sentiment,
            escalation_count = EXCLUDED.escalation_count,
            escalation_rate = EXCLUDED.escalation_rate,
            generated_at = NOW()
        RETURNING id
    """)

    import json
    result = await session.execute(
        stmt,
        {
            "report_date": report_date,
            "total_tickets": summary["total_tickets"],
            "tickets_by_channel": json.dumps(summary["tickets_by_channel"]),
            "top_topics": json.dumps(summary["top_topics"]),
            "mean_sentiment": summary["mean_sentiment"],
            "escalation_count": summary["escalation_count"],
            "escalation_rate": summary["escalation_rate"],
        },
    )
    await session.commit()

    report_id = result.scalar()

    # Return the full report
    report_result = await session.execute(
        select(DailyReport).where(DailyReport.report_date == report_date)
    )
    return report_result.scalar_one()
