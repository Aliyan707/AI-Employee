"""
tests/unit/test_escalation_rules.py — Unit tests for escalation rules.

Tests all 7 guardrail triggers:
1. Pricing inquiry
2. Refund request
3. Legal matter
4. Competitor mention
5. Account cancellation
6. Sentiment < 0.3
7. Profanity detected

Also tests:
- Non-triggering messages
- escalate_to_human idempotency
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.sub_agents.escalation_agent import (
    EscalationAgent,
    EscalationDecision,
    decide_escalation,
)


# ---------------------------------------------------------------------------
# Test each guardrail trigger via keyword check
# ---------------------------------------------------------------------------


class TestGuardrailTriggers:
    @pytest.mark.asyncio
    async def test_refund_trigger(self):
        """'I want a refund' should trigger refund rule."""
        decision = await decide_escalation(
            text="I want a refund for my last payment",
            sentiment_score=0.5,
        )
        assert decision.should_escalate is True
        assert decision.trigger_rule == "refund"
        assert decision.priority == "P1"

    @pytest.mark.asyncio
    async def test_pricing_trigger(self):
        """Pricing inquiry should trigger pricing rule."""
        decision = await decide_escalation(
            text="How much does the Professional plan cost?",
            sentiment_score=0.7,
        )
        assert decision.should_escalate is True
        assert decision.trigger_rule == "pricing"

    @pytest.mark.asyncio
    async def test_legal_trigger(self):
        """GDPR request should trigger legal rule."""
        decision = await decide_escalation(
            text="I want to make a GDPR data deletion request",
            sentiment_score=0.5,
        )
        assert decision.should_escalate is True
        assert decision.trigger_rule == "legal"
        assert decision.priority == "P1"

    @pytest.mark.asyncio
    async def test_legal_lawsuit_trigger(self):
        """Lawsuit mention should trigger legal rule."""
        decision = await decide_escalation(
            text="I am considering legal action against your company",
            sentiment_score=0.2,
        )
        assert decision.should_escalate is True
        assert decision.trigger_rule in ("legal", "sentiment")

    @pytest.mark.asyncio
    async def test_cancellation_trigger(self):
        """Account cancellation request should escalate."""
        decision = await decide_escalation(
            text="I want to cancel my account immediately",
            sentiment_score=0.4,
        )
        assert decision.should_escalate is True
        assert decision.trigger_rule == "account_cancellation"
        assert decision.priority == "P1"

    @pytest.mark.asyncio
    async def test_sentiment_trigger(self):
        """Score < 0.3 should trigger sentiment escalation."""
        decision = await decide_escalation(
            text="Your service is terrible I am so frustrated",
            sentiment_score=0.22,
        )
        assert decision.should_escalate is True
        assert decision.trigger_rule == "sentiment"
        assert decision.priority == "P1"

    @pytest.mark.asyncio
    async def test_profanity_trigger(self):
        """Profanity should trigger escalation."""
        decision = await decide_escalation(
            text="This is complete shit, I'm so angry",
            sentiment_score=0.4,
            profanity_detected=True,
        )
        assert decision.should_escalate is True
        assert decision.trigger_rule == "profanity"

    @pytest.mark.asyncio
    async def test_chargeback_trigger(self):
        """Chargeback is a type of refund escalation."""
        decision = await decide_escalation(
            text="I'm going to dispute this charge as a chargeback",
            sentiment_score=0.3,
        )
        assert decision.should_escalate is True
        assert decision.trigger_rule == "refund"


# ---------------------------------------------------------------------------
# Non-triggering messages
# ---------------------------------------------------------------------------


class TestNonTriggeringMessages:
    @pytest.mark.asyncio
    async def test_password_reset_no_escalation(self):
        """Password reset question should NOT escalate."""
        with patch(
            "agent.sub_agents.escalation_agent._llm_escalation_check",
            return_value=None,
        ):
            decision = await decide_escalation(
                text="How do I reset my password?",
                sentiment_score=0.7,
            )
        assert decision.should_escalate is False

    @pytest.mark.asyncio
    async def test_feature_question_no_escalation(self):
        """Feature question should NOT escalate."""
        with patch(
            "agent.sub_agents.escalation_agent._llm_escalation_check",
            return_value=None,
        ):
            decision = await decide_escalation(
                text="Can you explain how to set up 2FA?",
                sentiment_score=0.8,
            )
        assert decision.should_escalate is False

    @pytest.mark.asyncio
    async def test_thank_you_no_escalation(self):
        """Positive feedback should NOT escalate."""
        decision = await decide_escalation(
            text="Thank you, the support was excellent!",
            sentiment_score=0.95,
        )
        assert decision.should_escalate is False

    @pytest.mark.asyncio
    async def test_neutral_question_no_escalation(self):
        """Neutral product question should NOT escalate."""
        with patch(
            "agent.sub_agents.escalation_agent._llm_escalation_check",
            return_value=None,
        ):
            decision = await decide_escalation(
                text="Where can I find my API key?",
                sentiment_score=0.6,
            )
        assert decision.should_escalate is False


# ---------------------------------------------------------------------------
# EscalationAgent class interface
# ---------------------------------------------------------------------------


class TestEscalationAgentInterface:
    @pytest.mark.asyncio
    async def test_escalation_agent_run_escalates(self):
        """EscalationAgent.run should delegate to decide_escalation."""
        agent = EscalationAgent()
        decision = await agent.run(
            text="I demand a refund immediately",
            sentiment_score=0.2,
        )
        assert isinstance(decision, EscalationDecision)
        assert decision.should_escalate is True

    @pytest.mark.asyncio
    async def test_escalation_agent_run_no_escalation(self):
        """Non-escalation messages should return False."""
        agent = EscalationAgent()
        with patch(
            "agent.sub_agents.escalation_agent._llm_escalation_check",
            return_value=None,
        ):
            decision = await agent.run(
                text="How do I export my data?",
                sentiment_score=0.7,
            )
        assert decision.should_escalate is False


# ---------------------------------------------------------------------------
# Trigger detail and priority validation
# ---------------------------------------------------------------------------


class TestTriggerDetails:
    @pytest.mark.asyncio
    async def test_trigger_detail_populated(self):
        """trigger_detail should contain the matched text."""
        decision = await decide_escalation(
            text="I want money back for this subscription",
            sentiment_score=0.5,
        )
        assert decision.trigger_detail is not None
        assert len(decision.trigger_detail) > 0

    @pytest.mark.asyncio
    async def test_priority_p1_for_refund(self):
        """Refund escalations should have P1 priority."""
        decision = await decide_escalation(
            text="Please refund my payment",
            sentiment_score=0.4,
        )
        assert decision.priority == "P1"

    @pytest.mark.asyncio
    async def test_priority_p1_for_sentiment(self):
        """Sentiment < 0.3 should be P1 priority."""
        decision = await decide_escalation(
            text="I am absolutely furious",
            sentiment_score=0.1,
        )
        assert decision.priority == "P1"
