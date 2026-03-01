"""
api/routers/reports.py — Daily report API endpoints.

GET  /reports/daily/{date}     — get a specific day's report
POST /reports/daily/trigger    — queue immediate report generation
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import DailyReport
from database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class DailyReportResponse(BaseModel):
    id: str
    report_date: str
    total_tickets: int
    tickets_by_channel: dict
    top_topics: list
    mean_sentiment: Optional[float]
    escalation_count: int
    escalation_rate: Optional[float]
    generated_at: str


class TriggerResponse(BaseModel):
    accepted: bool
    message: str
    report_date: str


@router.get("/daily/{report_date}", response_model=DailyReportResponse)
async def get_daily_report(
    report_date: date,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the daily report for a specific date.

    Returns 404 for future dates or if no report has been generated yet.
    """
    today = date.today()

    if report_date > today:
        raise HTTPException(
            status_code=404,
            detail=f"No report available for future date {report_date}",
        )

    result = await db.execute(
        select(DailyReport).where(DailyReport.report_date == report_date)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"No report found for {report_date}. Run POST /reports/daily/trigger to generate.",
        )

    return DailyReportResponse(
        id=str(report.id),
        report_date=str(report.report_date),
        total_tickets=report.total_tickets,
        tickets_by_channel=report.tickets_by_channel or {},
        top_topics=report.top_topics or [],
        mean_sentiment=float(report.mean_sentiment) if report.mean_sentiment else None,
        escalation_count=report.escalation_count,
        escalation_rate=float(report.escalation_rate) if report.escalation_rate else None,
        generated_at=report.generated_at.isoformat() if report.generated_at else "",
    )


@router.post("/daily/trigger", response_model=TriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_daily_report(
    report_date: Optional[date] = Query(None, description="Date to generate report for (default: today)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger immediate generation of the daily report.

    If report_date not specified, generates report for today.
    Uses the request's existing DB session for immediate execution.
    """
    target_date = report_date or date.today()

    if target_date > date.today():
        raise HTTPException(
            status_code=400,
            detail="Cannot generate report for a future date",
        )

    await _generate_report_sync(target_date, session=db)
    logger.info("Report generated for %s", target_date)

    return TriggerResponse(
        accepted=True,
        message=f"Report generated for {target_date}",
        report_date=str(target_date),
    )


async def _generate_report_sync(target_date: date, session: AsyncSession) -> None:
    """Generate and persist the daily report for target_date using an existing session."""
    from database.repositories.metrics_repo import get_daily_summary, upsert_daily_report

    summary = await get_daily_summary(session, target_date)
    await upsert_daily_report(session, target_date, summary)
    logger.info("Report generated for %s: %d tickets", target_date, summary["total_tickets"])
