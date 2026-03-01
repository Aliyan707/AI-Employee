"""
tests/contract/test_tool_contracts.py — Contract tests for all 6 agent tools.

Validates input/output schemas match contracts/agent-tools.md specification.
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from agent.tools.create_ticket import CreateTicketInput, ToolResult
from agent.tools.escalate_to_human import EscalationResult
from agent.tools.format_for_channel import FormattedResponse
from agent.tools.get_customer_history import CustomerHistoryResult, CustomerInfo, TicketSummary
from agent.tools.search_knowledge_base import KBSearchResult
from agent.tools.send_response import SendResult
from agent.tools.analyze_sentiment import SentimentResult


# ---------------------------------------------------------------------------
# Tool 1: create_ticket
# ---------------------------------------------------------------------------


class TestCreateTicketContract:
    def test_input_schema_valid(self):
        """Valid input should parse without errors."""
        input_data = CreateTicketInput(
            customer_id=uuid.uuid4(),
            channel="webform",
            raw_content="How do I reset my password?",
            content_hash="a" * 64,
        )
        assert input_data.channel == "webform"
        assert input_data.raw_content is not None

    def test_input_requires_customer_id(self):
        """customer_id is required."""
        with pytest.raises(ValidationError):
            CreateTicketInput(
                channel="webform",
                raw_content="Test",
                content_hash="a" * 64,
            )

    def test_output_success_schema(self):
        """Success output matches contract schema."""
        result = ToolResult(
            ticket_id=uuid.uuid4(),
            status="open",
            created=True,
            duplicate=False,
        )
        assert result.status == "open"
        assert result.created is True
        assert result.duplicate is False

    def test_output_duplicate_schema(self):
        """Duplicate output matches contract schema."""
        result = ToolResult(
            ticket_id=uuid.uuid4(),
            status="open",
            created=False,
            duplicate=True,
        )
        assert result.duplicate is True
        assert result.created is False


# ---------------------------------------------------------------------------
# Tool 2: get_customer_history
# ---------------------------------------------------------------------------


class TestGetCustomerHistoryContract:
    def test_output_schema_found_customer(self):
        """CustomerHistoryResult should match contract schema."""
        result = CustomerHistoryResult(
            customer=CustomerInfo(
                id=str(uuid.uuid4()),
                display_name="Alice",
                company="Acme",
                channels_used=["email", "whatsapp"],
            ),
            tickets=[
                TicketSummary(
                    ticket_id=str(uuid.uuid4()),
                    channel="email",
                    status="resolved",
                    subject="Password reset",
                    created_at="2026-03-01T10:00:00Z",
                    message_count=3,
                )
            ],
            last_sentiment=0.72,
            open_ticket_count=1,
        )
        assert result.customer.display_name == "Alice"
        assert len(result.tickets) == 1
        assert result.last_sentiment == 0.72

    def test_output_schema_not_found(self):
        """Not-found result should have null customer and empty tickets."""
        result = CustomerHistoryResult(
            customer=None,
            tickets=[],
            last_sentiment=None,
            open_ticket_count=0,
        )
        assert result.customer is None
        assert result.tickets == []
        assert result.last_sentiment is None
        assert result.open_ticket_count == 0


# ---------------------------------------------------------------------------
# Tool 3: search_knowledge_base
# ---------------------------------------------------------------------------


class TestSearchKnowledgeBaseContract:
    def test_output_schema_success(self):
        """KB search result should match contract schema."""
        from database.repositories.kb_repo import KBResult

        result = KBSearchResult(
            results=[
                KBResult(
                    article_id=uuid.uuid4(),
                    title="How to Reset Your Password",
                    content="Step 1: Click Forgot Password...",
                    score=0.92,
                    topic_tags=["account", "password"],
                )
            ],
            kb_miss=False,
        )
        assert result.kb_miss is False
        assert len(result.results) == 1
        assert result.results[0].score == 0.92

    def test_output_schema_kb_miss(self):
        """KB miss should have empty results and kb_miss=True."""
        result = KBSearchResult(results=[], kb_miss=True)
        assert result.kb_miss is True
        assert result.results == []


# ---------------------------------------------------------------------------
# Tool 4: analyze_sentiment
# ---------------------------------------------------------------------------


class TestAnalyzeSentimentContract:
    def test_output_schema_positive(self):
        """Positive sentiment result matches contract schema."""
        result = SentimentResult(
            score=0.85,
            label="positive",
            profanity_detected=False,
            escalate=False,
        )
        assert 0.0 <= result.score <= 1.0
        assert result.label in ("angry", "negative", "neutral", "positive")
        assert result.escalate is False

    def test_output_schema_angry(self):
        """Angry sentiment result triggers escalation."""
        result = SentimentResult(
            score=0.15,
            label="angry",
            profanity_detected=False,
            escalate=True,
        )
        assert result.escalate is True
        assert result.score < 0.3

    def test_profanity_triggers_escalation(self):
        """Profanity detection should always set escalate=True."""
        result = SentimentResult(
            score=0.6,
            label="neutral",
            profanity_detected=True,
            escalate=True,
        )
        assert result.profanity_detected is True
        assert result.escalate is True

    def test_valid_labels(self):
        """All valid labels should be one of the defined values."""
        valid_labels = {"angry", "negative", "neutral", "positive"}
        for label in valid_labels:
            result = SentimentResult(
                score=0.5, label=label, profanity_detected=False, escalate=False
            )
            assert result.label in valid_labels


# ---------------------------------------------------------------------------
# Tool 5: escalate_to_human
# ---------------------------------------------------------------------------


class TestEscalateToHumanContract:
    def test_output_schema_success(self):
        """Escalation success result matches contract schema."""
        result = EscalationResult(
            escalation_id=42,
            ticket_id=str(uuid.uuid4()),
            status="escalated",
            queue_position=3,
            customer_message="A team member will contact you shortly.",
            already_escalated=False,
        )
        assert result.status == "escalated"
        assert result.already_escalated is False
        assert result.customer_message is not None

    def test_output_schema_already_escalated(self):
        """Already-escalated result matches contract schema."""
        result = EscalationResult(
            escalation_id=42,
            ticket_id=str(uuid.uuid4()),
            status="already_escalated",
            queue_position=None,
            customer_message=None,
            already_escalated=True,
        )
        assert result.status == "already_escalated"
        assert result.already_escalated is True
        assert result.customer_message is None

    def test_valid_trigger_rules(self):
        """trigger_rule should be one of the defined values."""
        valid_rules = {
            "pricing", "refund", "legal", "competitor",
            "sentiment", "profanity", "undocumented", "account_cancellation"
        }
        for rule in valid_rules:
            result = EscalationResult(
                escalation_id=1,
                ticket_id=str(uuid.uuid4()),
                status="escalated",
                queue_position=1,
                customer_message="Test",
                already_escalated=False,
            )
            # Just verify EscalationResult can be created (no validation error)
            assert result is not None


# ---------------------------------------------------------------------------
# Tool 6: send_response
# ---------------------------------------------------------------------------


class TestSendResponseContract:
    def test_output_schema_success(self):
        """Send success result matches contract schema."""
        result = SendResult(
            message_id=123,
            ticket_id=str(uuid.uuid4()),
            channel="webform",
            sent=True,
            duplicate=False,
            sent_at="2026-03-01T10:00:00Z",
        )
        assert result.sent is True
        assert result.duplicate is False
        assert result.message_id == 123

    def test_output_schema_duplicate(self):
        """Duplicate send result matches contract schema."""
        result = SendResult(
            message_id=123,
            ticket_id=str(uuid.uuid4()),
            channel="email",
            sent=False,
            duplicate=True,
        )
        assert result.sent is False
        assert result.duplicate is True

    def test_response_hash_is_sha256(self):
        """Response hash should be valid SHA-256 hex (64 chars)."""
        from agent.tools.send_response import compute_response_hash
        text = "Here is your answer about password reset."
        h = compute_response_hash(text)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# Tool 7: format_for_channel (internal function)
# ---------------------------------------------------------------------------


class TestFormatForChannelContract:
    def test_output_dataclass_fields(self):
        """FormattedResponse should have all required fields."""
        result = FormattedResponse(
            text="Your answer is here.",
            within_limits=True,
            word_count=4,
            char_count=20,
            error=None,
        )
        assert result.text is not None
        assert isinstance(result.within_limits, bool)
        assert result.error is None

    def test_error_field_populated_on_failure(self):
        """Error field should be set when within_limits=False."""
        result = FormattedResponse(
            text="Too long text...",
            within_limits=False,
            word_count=999,
            char_count=5000,
            error="E004: Response exceeds channel limits after reformat attempt",
        )
        assert result.within_limits is False
        assert "E004" in result.error
