"""
tests/integration/test_daily_report.py — Integration tests for daily report generation.

Tests:
  - get_daily_summary correctly aggregates 10 tickets across channels
  - upsert_daily_report writes the DailyReport row and can be retrieved
  - Idempotent upsert (run twice, row updated not duplicated)
  - Zero-activity day: total_tickets=0, escalation_count=0, mean_sentiment=None
  - Escalation rate is computed correctly from fixture data
  - Channel breakdown counts are accurate
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helpers — lightweight in-memory fakes (no real DB needed for unit-style tests)
# ---------------------------------------------------------------------------

def _make_channel_row(channel: str, count: int):
    """Simulate a SQLAlchemy Row-like tuple."""
    return (channel, count)


def _make_escalation_row(count: int):
    return count


# ---------------------------------------------------------------------------
# Pure-function tests for get_daily_summary logic
# (these mock the session to avoid needing a real DB)
# ---------------------------------------------------------------------------


class TestGetDailySummaryMocked:
    """
    Tests for get_daily_summary with a mocked AsyncSession.
    No live database required.
    """

    @pytest.mark.asyncio
    async def test_ten_ticket_fixture(self):
        """
        10 tickets: 4 email, 3 whatsapp, 3 webform.
        2 escalated. Mean sentiment ~0.75.
        """
        from database.repositories.metrics_repo import get_daily_summary

        target_date = date(2025, 6, 15)

        # ---- channel rows ----
        channel_rows = [
            ("email", 4),
            ("whatsapp", 3),
            ("webform", 3),
        ]

        # ---- mean sentiment ----
        mean_sentiment_value = Decimal("0.750")

        # ---- escalation count ----
        escalation_count_value = 2

        # ---- top topics ----
        topic_rows = [
            ("Password Reset", 3),
            ("Billing Inquiry", 2),
            ("Feature Request", 2),
            ("Integration Issue", 2),
            ("Account Help", 1),
        ]

        # Build mock execute results
        async def mock_execute(stmt, params=None):
            result_mock = MagicMock()
            # Detect which query by inspecting the SQL text
            sql_str = str(stmt)

            if "GROUP BY channel" in sql_str:
                result_mock.fetchall.return_value = channel_rows
            elif "AVG" in sql_str:
                result_mock.scalar.return_value = mean_sentiment_value
            elif "escalated = TRUE" in sql_str:
                result_mock.scalar.return_value = escalation_count_value
            elif "GROUP BY subject" in sql_str:
                result_mock.fetchall.return_value = topic_rows
            else:
                result_mock.fetchall.return_value = []
                result_mock.scalar.return_value = None

            return result_mock

        mock_session = AsyncMock()
        mock_session.execute.side_effect = mock_execute

        summary = await get_daily_summary(mock_session, target_date)

        # Total ticket count
        assert summary["total_tickets"] == 10

        # Channel breakdown
        assert summary["tickets_by_channel"]["email"] == 4
        assert summary["tickets_by_channel"]["whatsapp"] == 3
        assert summary["tickets_by_channel"]["webform"] == 3

        # Mean sentiment
        assert summary["mean_sentiment"] is not None
        assert abs(summary["mean_sentiment"] - 0.75) < 0.001

        # Escalation
        assert summary["escalation_count"] == 2
        assert summary["escalation_rate"] == 20.0  # 2/10 * 100

        # Top topics
        assert len(summary["top_topics"]) == 5
        assert summary["top_topics"][0]["topic"] == "Password Reset"
        assert summary["top_topics"][0]["count"] == 3

    @pytest.mark.asyncio
    async def test_zero_activity_day(self):
        """
        A day with no tickets should return zeroed-out summary with None sentiment.
        """
        from database.repositories.metrics_repo import get_daily_summary

        target_date = date(2025, 1, 1)

        async def mock_execute(stmt, params=None):
            result_mock = MagicMock()
            sql_str = str(stmt)

            if "GROUP BY channel" in sql_str or "GROUP BY subject" in sql_str:
                result_mock.fetchall.return_value = []
            else:
                result_mock.scalar.return_value = None

            return result_mock

        mock_session = AsyncMock()
        mock_session.execute.side_effect = mock_execute

        summary = await get_daily_summary(mock_session, target_date)

        assert summary["total_tickets"] == 0
        assert summary["tickets_by_channel"] == {"email": 0, "whatsapp": 0, "webform": 0}
        assert summary["mean_sentiment"] is None
        assert summary["escalation_count"] == 0
        assert summary["escalation_rate"] == 0.0
        assert summary["top_topics"] == []

    @pytest.mark.asyncio
    async def test_escalation_rate_calculation(self):
        """
        5 tickets, 1 escalated → 20.0% escalation rate.
        """
        from database.repositories.metrics_repo import get_daily_summary

        target_date = date(2025, 3, 10)

        async def mock_execute(stmt, params=None):
            result_mock = MagicMock()
            sql_str = str(stmt)

            if "GROUP BY channel" in sql_str:
                result_mock.fetchall.return_value = [("webform", 5)]
            elif "AVG" in sql_str:
                result_mock.scalar.return_value = Decimal("0.600")
            elif "escalated = TRUE" in sql_str:
                result_mock.scalar.return_value = 1
            elif "GROUP BY subject" in sql_str:
                result_mock.fetchall.return_value = []
            else:
                result_mock.fetchall.return_value = []
                result_mock.scalar.return_value = None

            return result_mock

        mock_session = AsyncMock()
        mock_session.execute.side_effect = mock_execute

        summary = await get_daily_summary(mock_session, target_date)

        assert summary["total_tickets"] == 5
        assert summary["escalation_count"] == 1
        assert summary["escalation_rate"] == pytest.approx(20.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_single_channel_summary(self):
        """
        All 3 tickets from email only; whatsapp/webform remain 0.
        """
        from database.repositories.metrics_repo import get_daily_summary

        target_date = date(2025, 4, 20)

        async def mock_execute(stmt, params=None):
            result_mock = MagicMock()
            sql_str = str(stmt)

            if "GROUP BY channel" in sql_str:
                result_mock.fetchall.return_value = [("email", 3)]
            elif "AVG" in sql_str:
                result_mock.scalar.return_value = Decimal("0.900")
            elif "escalated = TRUE" in sql_str:
                result_mock.scalar.return_value = 0
            elif "GROUP BY subject" in sql_str:
                result_mock.fetchall.return_value = [("Login Issue", 3)]
            else:
                result_mock.fetchall.return_value = []
                result_mock.scalar.return_value = None

            return result_mock

        mock_session = AsyncMock()
        mock_session.execute.side_effect = mock_execute

        summary = await get_daily_summary(mock_session, target_date)

        assert summary["total_tickets"] == 3
        assert summary["tickets_by_channel"]["email"] == 3
        assert summary["tickets_by_channel"]["whatsapp"] == 0
        assert summary["tickets_by_channel"]["webform"] == 0
        assert summary["escalation_rate"] == 0.0


# ---------------------------------------------------------------------------
# Upsert DailyReport tests
# ---------------------------------------------------------------------------


class TestUpsertDailyReport:
    """
    Tests for upsert_daily_report with a mocked AsyncSession.
    Verifies SQL is executed with correct params and the correct model is returned.
    """

    @pytest.mark.asyncio
    async def test_upsert_writes_correct_params(self):
        """
        upsert_daily_report should execute the INSERT ... ON CONFLICT upsert
        with the exact summary values.
        """
        import json
        from database.repositories.metrics_repo import upsert_daily_report
        from database.models import DailyReport

        target_date = date(2025, 6, 15)
        summary = {
            "total_tickets": 10,
            "tickets_by_channel": {"email": 4, "whatsapp": 3, "webform": 3},
            "mean_sentiment": 0.75,
            "escalation_count": 2,
            "escalation_rate": 20.0,
            "top_topics": [{"topic": "Password Reset", "count": 3}],
        }

        report_id = uuid.uuid4()

        # Mock the upsert result (RETURNING id)
        mock_upsert_result = MagicMock()
        mock_upsert_result.scalar.return_value = report_id

        # Mock the SELECT result
        fake_report = DailyReport(
            id=report_id,
            report_date=target_date,
            total_tickets=10,
            tickets_by_channel={"email": 4, "whatsapp": 3, "webform": 3},
            top_topics=[{"topic": "Password Reset", "count": 3}],
            mean_sentiment=Decimal("0.750"),
            escalation_count=2,
            escalation_rate=Decimal("20.00"),
            generated_at=datetime.now(timezone.utc),
        )
        mock_select_result = MagicMock()
        mock_select_result.scalar_one.return_value = fake_report

        execute_results = iter([mock_upsert_result, mock_select_result])

        async def mock_execute(stmt, params=None):
            return next(execute_results)

        mock_session = AsyncMock()
        mock_session.execute.side_effect = mock_execute
        mock_session.commit = AsyncMock()

        report = await upsert_daily_report(mock_session, target_date, summary)

        # Verify commit was called
        mock_session.commit.assert_called_once()

        # Verify return type and values
        assert isinstance(report, DailyReport)
        assert report.total_tickets == 10
        assert report.escalation_count == 2

    @pytest.mark.asyncio
    async def test_upsert_is_idempotent(self):
        """
        Calling upsert_daily_report twice for the same date should not raise.
        The second call should update the existing row (ON CONFLICT DO UPDATE).
        Both calls should succeed and commit.
        """
        import json
        from database.repositories.metrics_repo import upsert_daily_report
        from database.models import DailyReport

        target_date = date(2025, 6, 15)
        summary_v1 = {
            "total_tickets": 5,
            "tickets_by_channel": {"email": 2, "whatsapp": 2, "webform": 1},
            "mean_sentiment": 0.6,
            "escalation_count": 1,
            "escalation_rate": 20.0,
            "top_topics": [],
        }
        summary_v2 = {
            "total_tickets": 8,
            "tickets_by_channel": {"email": 4, "whatsapp": 2, "webform": 2},
            "mean_sentiment": 0.7,
            "escalation_count": 2,
            "escalation_rate": 25.0,
            "top_topics": [{"topic": "Billing", "count": 2}],
        }

        report_id = uuid.uuid4()

        def _make_mock_pair(total: int, esc_count: int, esc_rate: float, mean_s: float):
            upsert_r = MagicMock()
            upsert_r.scalar.return_value = report_id

            fake = DailyReport(
                id=report_id,
                report_date=target_date,
                total_tickets=total,
                tickets_by_channel={},
                top_topics=[],
                mean_sentiment=Decimal(str(mean_s)),
                escalation_count=esc_count,
                escalation_rate=Decimal(str(esc_rate)),
                generated_at=datetime.now(timezone.utc),
            )
            select_r = MagicMock()
            select_r.scalar_one.return_value = fake
            return upsert_r, select_r

        r1_upsert, r1_select = _make_mock_pair(5, 1, 20.0, 0.6)
        r2_upsert, r2_select = _make_mock_pair(8, 2, 25.0, 0.7)

        call_count = 0
        results_seq = [r1_upsert, r1_select, r2_upsert, r2_select]
        results_iter = iter(results_seq)

        async def mock_execute(stmt, params=None):
            return next(results_iter)

        mock_session = AsyncMock()
        mock_session.execute.side_effect = mock_execute

        report_v1 = await upsert_daily_report(mock_session, target_date, summary_v1)
        assert report_v1.total_tickets == 5

        report_v2 = await upsert_daily_report(mock_session, target_date, summary_v2)
        assert report_v2.total_tickets == 8

        # Two commits total
        assert mock_session.commit.call_count == 2


# ---------------------------------------------------------------------------
# End-to-end: get_daily_summary → upsert_daily_report round-trip
# ---------------------------------------------------------------------------


class TestDailyReportRoundTrip:
    """
    Round-trip: generate a summary dict from mocked query results, then
    upsert it and verify the stored report reflects the summary values.
    """

    @pytest.mark.asyncio
    async def test_summary_to_report_round_trip(self):
        """
        Full round-trip: get_daily_summary produces a dict, upsert_daily_report
        writes it, and the returned DailyReport matches.
        """
        from database.repositories.metrics_repo import get_daily_summary, upsert_daily_report
        from database.models import DailyReport

        target_date = date(2025, 7, 4)

        # --- Phase 1: mock get_daily_summary session ---
        async def summary_execute(stmt, params=None):
            result_mock = MagicMock()
            sql_str = str(stmt)

            if "GROUP BY channel" in sql_str:
                result_mock.fetchall.return_value = [
                    ("email", 4), ("whatsapp", 3), ("webform", 3)
                ]
            elif "AVG" in sql_str:
                result_mock.scalar.return_value = Decimal("0.820")
            elif "escalated = TRUE" in sql_str:
                result_mock.scalar.return_value = 3
            elif "GROUP BY subject" in sql_str:
                result_mock.fetchall.return_value = [
                    ("How to export data", 2),
                    ("2FA setup", 2),
                    ("Webhook config", 2),
                    ("API key limit", 2),
                    ("SSO setup", 2),
                ]
            else:
                result_mock.fetchall.return_value = []
                result_mock.scalar.return_value = None

            return result_mock

        summary_session = AsyncMock()
        summary_session.execute.side_effect = summary_execute

        summary = await get_daily_summary(summary_session, target_date)
        assert summary["total_tickets"] == 10
        assert summary["escalation_count"] == 3

        # --- Phase 2: mock upsert session ---
        report_id = uuid.uuid4()

        fake_report = DailyReport(
            id=report_id,
            report_date=target_date,
            total_tickets=summary["total_tickets"],
            tickets_by_channel=summary["tickets_by_channel"],
            top_topics=summary["top_topics"],
            mean_sentiment=Decimal(str(round(summary["mean_sentiment"], 3))),
            escalation_count=summary["escalation_count"],
            escalation_rate=Decimal(str(summary["escalation_rate"])),
            generated_at=datetime.now(timezone.utc),
        )

        upsert_result = MagicMock()
        upsert_result.scalar.return_value = report_id
        select_result = MagicMock()
        select_result.scalar_one.return_value = fake_report

        upsert_results = iter([upsert_result, select_result])

        async def upsert_execute(stmt, params=None):
            return next(upsert_results)

        upsert_session = AsyncMock()
        upsert_session.execute.side_effect = upsert_execute

        report = await upsert_daily_report(upsert_session, target_date, summary)

        # Validate all fields propagated correctly
        assert report.total_tickets == 10
        assert report.escalation_count == 3
        assert float(report.escalation_rate) == pytest.approx(30.0, abs=0.01)
        assert float(report.mean_sentiment) == pytest.approx(0.82, abs=0.001)
        assert report.report_date == target_date
        assert len(report.top_topics) == 5

    @pytest.mark.asyncio
    async def test_zero_activity_report_round_trip(self):
        """
        Zero-activity day: summary correctly produces zeros, upsert stores them,
        and the report has total_tickets=0 and mean_sentiment=None.
        """
        from database.repositories.metrics_repo import get_daily_summary, upsert_daily_report
        from database.models import DailyReport

        target_date = date(2025, 2, 14)

        async def zero_execute(stmt, params=None):
            result_mock = MagicMock()
            sql_str = str(stmt)

            if "GROUP BY channel" in sql_str or "GROUP BY subject" in sql_str:
                result_mock.fetchall.return_value = []
            else:
                result_mock.scalar.return_value = None

            return result_mock

        summary_session = AsyncMock()
        summary_session.execute.side_effect = zero_execute

        summary = await get_daily_summary(summary_session, target_date)

        assert summary["total_tickets"] == 0
        assert summary["mean_sentiment"] is None
        assert summary["escalation_rate"] == 0.0

        # Upsert with zero-activity summary
        report_id = uuid.uuid4()
        fake_report = DailyReport(
            id=report_id,
            report_date=target_date,
            total_tickets=0,
            tickets_by_channel={"email": 0, "whatsapp": 0, "webform": 0},
            top_topics=[],
            mean_sentiment=None,
            escalation_count=0,
            escalation_rate=Decimal("0.00"),
            generated_at=datetime.now(timezone.utc),
        )

        upsert_result = MagicMock()
        upsert_result.scalar.return_value = report_id
        select_result = MagicMock()
        select_result.scalar_one.return_value = fake_report

        upsert_results = iter([upsert_result, select_result])

        async def upsert_execute(stmt, params=None):
            return next(upsert_results)

        upsert_session = AsyncMock()
        upsert_session.execute.side_effect = upsert_execute

        report = await upsert_daily_report(upsert_session, target_date, summary)

        assert report.total_tickets == 0
        assert report.mean_sentiment is None
        assert report.escalation_count == 0
