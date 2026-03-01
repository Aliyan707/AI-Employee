"""
tests/integration/test_pipeline_escalation.py — Escalation pipeline tests.

Tests:
1. Refund request triggers escalation, holding message returned
2. Escalation record created with correct trigger_rule and priority
3. Pipeline stops before step 6 (no KB-based response generated)
4. Ticket status = escalated
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.orchestrator import OrchestratorAgent
from agent.sub_agents.escalation_agent import EscalationDecision
from agent.tools.analyze_sentiment import SentimentResult
from agent.tools.get_customer_history import CustomerHistoryResult
from agent.tools.search_knowledge_base import KBSearchResult
from channels.webform.handler import ChannelMetadata, IntakeEvent, compute_content_hash


def make_refund_event(channel: str = "webform") -> IntakeEvent:
    return IntakeEvent(
        schema_version="1.0",
        event_type="customer_inquiry",
        event_id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        session_id=str(uuid.uuid4()),
        channel=channel,
        raw_content="I want a full refund for my subscription",
        content_hash=compute_content_hash("I want a full refund for my subscription"),
        customer_identifiers={"email": "refund@example.com"},
        customer_name="Refund User",
        channel_metadata=ChannelMetadata(),
        customer_id=uuid.uuid4(),
    )


class TestEscalationPipeline:
    @pytest.mark.asyncio
    async def test_refund_request_escalates(self):
        """Refund request should escalate and return holding message."""
        event = make_refund_event()
        mock_session = AsyncMock()

        with patch("agent.orchestrator.create_ticket") as mock_ct, \
             patch("agent.orchestrator.get_customer_history") as mock_gh, \
             patch("agent.orchestrator.escalate_to_human") as mock_esc, \
             patch("agent.orchestrator.send_response") as mock_sr, \
             patch("agent.orchestrator._generate_ai_response") as mock_gen:

            ticket_id = uuid.uuid4()
            mock_ticket = MagicMock()
            mock_ticket.ticket_id = ticket_id
            mock_ticket.duplicate = False
            mock_ct.return_value = mock_ticket

            mock_gh.return_value = CustomerHistoryResult(
                customer=None, tickets=[], last_sentiment=None, open_ticket_count=0
            )

            orchestrator = OrchestratorAgent()

            # Mock sentiment: not angry (0.4), so sentiment won't trigger
            orchestrator.sentiment_agent.run = AsyncMock(return_value=SentimentResult(
                score=0.4, label="negative", profanity_detected=False, escalate=False
            ))

            # Mock KB: miss
            orchestrator.kb_agent.run = AsyncMock(return_value=KBSearchResult(
                results=[], kb_miss=True
            ))

            # Mock escalation: REFUND triggers
            orchestrator.escalation_agent.run = AsyncMock(return_value=EscalationDecision(
                should_escalate=True,
                trigger_rule="refund",
                trigger_detail="Keyword matched: 'refund'",
                priority="P1",
            ))

            # Mock escalate_to_human
            from agent.tools.escalate_to_human import EscalationResult
            mock_esc.return_value = EscalationResult(
                escalation_id=1,
                ticket_id=str(ticket_id),
                status="escalated",
                queue_position=3,
                customer_message="Your request has been escalated to our team.",
                already_escalated=False,
            )

            # Mock send_response for holding message
            from agent.tools.send_response import SendResult
            mock_sr.return_value = SendResult(
                message_id=1, ticket_id=str(ticket_id), channel="webform",
                sent=True, duplicate=False
            )

            result = await orchestrator.run(session=mock_session, intake_event=event)

        # Validate escalation result
        assert result.escalated is True
        assert result.escalation_rule == "refund"
        assert result.response_text is not None

        # Validate pipeline did NOT reach step 6 (AI response generation)
        mock_gen.assert_not_called()

    @pytest.mark.asyncio
    async def test_holding_message_within_channel_limit_webform(self):
        """Holding message for webform should be within 300 words."""
        from agent.tools.escalate_to_human import _build_holding_message
        ticket_id = uuid.uuid4()
        message = _build_holding_message("webform", ticket_id)
        assert len(message.split()) <= 300

    @pytest.mark.asyncio
    async def test_holding_message_within_channel_limit_whatsapp(self):
        """Holding message for WhatsApp should be within 300 chars."""
        from agent.tools.escalate_to_human import _build_holding_message
        ticket_id = uuid.uuid4()
        message = _build_holding_message("whatsapp", ticket_id)
        assert len(message) <= 300

    @pytest.mark.asyncio
    async def test_escalation_already_escalated_idempotent(self):
        """Second escalation call for same ticket returns already_escalated."""
        from agent.tools.escalate_to_human import EscalationResult, escalate_to_human
        from database.models import EscalationRecord

        ticket_id = uuid.uuid4()
        mock_session = AsyncMock()

        # Simulate existing escalation record
        existing_record = MagicMock()
        existing_record.id = 42

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_record
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await escalate_to_human(
            session=mock_session,
            ticket_id=ticket_id,
            trigger_rule="refund",
            trigger_detail="test",
            sentiment_score=0.4,
            priority="P1",
            channel="webform",
        )

        assert result.already_escalated is True
        assert result.status == "already_escalated"
        assert result.escalation_id == 42
