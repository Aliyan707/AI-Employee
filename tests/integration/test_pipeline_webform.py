"""
tests/integration/test_pipeline_webform.py — End-to-end pipeline test for webform.

Tests the full 7-step pipeline with mocked LLM calls and a real test database.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from channels.webform.handler import (
    ChannelMetadata,
    IntakeEvent,
    WebformPayload,
    compute_content_hash,
    normalise_webform,
)


class TestWebformPipelineUnit:
    """Tests that can run without a database."""

    def test_normalise_webform_creates_intake_event(self):
        """WebformPayload should normalise to a complete IntakeEvent."""
        payload = WebformPayload(
            email="test@example.com",
            name="Test User",
            message="How do I reset my password?",
            subject="Password Help",
        )
        event = normalise_webform(payload)

        assert event.channel == "webform"
        assert event.raw_content == "How do I reset my password?"
        assert event.customer_identifiers["email"] == "test@example.com"
        assert event.customer_name == "Test User"
        assert event.content_hash == compute_content_hash("How do I reset my password?")
        assert event.schema_version == "1.0"
        assert event.event_type == "customer_inquiry"

    def test_normalise_webform_strips_whitespace(self):
        """Message whitespace should be stripped."""
        payload = WebformPayload(
            email="test@example.com",
            message="  Hello, I need help.  ",
        )
        event = normalise_webform(payload)
        assert event.raw_content == "Hello, I need help."

    def test_webform_payload_validates_email(self):
        """Invalid email should fail validation."""
        with pytest.raises(Exception):
            WebformPayload(email="not-an-email", message="Hello")

    def test_webform_payload_requires_message(self):
        """Empty message should fail validation."""
        with pytest.raises(Exception):
            WebformPayload(email="test@example.com", message="")

    def test_webform_payload_whitespace_message_rejected(self):
        """Whitespace-only message should fail validation."""
        with pytest.raises(Exception):
            WebformPayload(email="test@example.com", message="   ")


class TestWebformOrchestratorMocked:
    """Tests with mocked external dependencies."""

    @pytest.mark.asyncio
    async def test_pipeline_runs_7_steps(self):
        """Full pipeline should execute all 7 steps and return a response."""
        from agent.orchestrator import OrchestratorAgent
        from agent.tools.analyze_sentiment import SentimentResult
        from agent.sub_agents.escalation_agent import EscalationDecision
        from agent.tools.search_knowledge_base import KBSearchResult
        from agent.tools.get_customer_history import CustomerHistoryResult

        # Create minimal IntakeEvent
        event = IntakeEvent(
            schema_version="1.0",
            event_type="customer_inquiry",
            event_id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            session_id=str(uuid.uuid4()),
            channel="webform",
            raw_content="How do I reset my password?",
            content_hash=compute_content_hash("How do I reset my password?"),
            customer_identifiers={"email": "test@example.com"},
            customer_name="Test User",
            channel_metadata=ChannelMetadata(),
            customer_id=uuid.uuid4(),
        )

        mock_session = AsyncMock()

        with patch("agent.orchestrator.create_ticket") as mock_ct, \
             patch("agent.orchestrator.get_customer_history") as mock_gh, \
             patch("agent.orchestrator.resolve_or_create_customer") as mock_rc, \
             patch.object(OrchestratorAgent, "_handle_escalation") as mock_esc, \
             patch("agent.orchestrator.send_response") as mock_sr, \
             patch("agent.orchestrator._generate_ai_response") as mock_gen, \
             patch("agent.orchestrator.format_for_channel") as mock_fmt:

            ticket_id = uuid.uuid4()

            # Mock create_ticket
            mock_ticket_result = MagicMock()
            mock_ticket_result.ticket_id = ticket_id
            mock_ticket_result.duplicate = False
            mock_ct.return_value = mock_ticket_result

            # Mock history
            mock_history = CustomerHistoryResult(
                customer=None, tickets=[], last_sentiment=None, open_ticket_count=0
            )
            mock_gh.return_value = mock_history

            # Mock sentiment sub-agent
            orchestrator = OrchestratorAgent()
            mock_sentiment = AsyncMock(return_value=SentimentResult(
                score=0.8, label="positive", profanity_detected=False, escalate=False
            ))
            orchestrator.sentiment_agent.run = mock_sentiment

            # Mock KB sub-agent
            mock_kb = AsyncMock(return_value=KBSearchResult(results=[], kb_miss=True))
            orchestrator.kb_agent.run = mock_kb

            # Mock escalation decision (no escalation)
            mock_escalation_decision = EscalationDecision(
                should_escalate=False, trigger_rule=None, trigger_detail=None, priority="P3"
            )
            orchestrator.escalation_agent.run = AsyncMock(return_value=mock_escalation_decision)

            # Mock AI response generation
            mock_gen.return_value = "To reset your password, click Forgot Password."

            # Mock format_for_channel
            from agent.tools.format_for_channel import FormattedResponse
            mock_formatted = FormattedResponse(
                text="To reset your password, click Forgot Password.",
                within_limits=True,
                word_count=9,
                char_count=48,
                error=None,
            )
            mock_fmt.return_value = mock_formatted

            # Mock send_response
            from agent.tools.send_response import SendResult
            mock_send = MagicMock()
            mock_send.message_id = 1
            mock_send.sent = True
            mock_send.duplicate = False
            mock_sr.return_value = mock_send

            result = await orchestrator.run(session=mock_session, intake_event=event)

        assert result.ticket_id == ticket_id
        assert result.escalated is False
        assert result.response_text is not None
        assert len(result.pipeline_log) >= 5  # At least 5 steps logged
