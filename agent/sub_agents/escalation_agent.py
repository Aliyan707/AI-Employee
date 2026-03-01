"""
agent/sub_agents/escalation_agent.py — Escalation decision sub-agent.

Classifies whether a customer message requires human escalation.
Uses keyword pre-check for speed, then GPT-4o for ambiguous cases.
Returns EscalationDecision with trigger rule, detail, and priority.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
openai_client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)


@dataclass
class EscalationDecision:
    """Result of escalation classification."""
    should_escalate: bool
    trigger_rule: Optional[str]   # pricing|refund|legal|competitor|sentiment|profanity|undocumented
    trigger_detail: Optional[str] # specific text that triggered the rule
    priority: str                  # P1|P2|P3


# ---------------------------------------------------------------------------
# Keyword rule definitions
# ---------------------------------------------------------------------------

ESCALATION_RULES = {
    "refund": {
        "keywords": [
            "refund", "money back", "chargeback", "charge back", "get my money",
            "reimburse", "reimbursement", "return my money", "cancel and refund",
        ],
        "priority": "P1",
    },
    "pricing": {
        "keywords": [
            "how much", "what does it cost", "pricing", "price", "cost",
            "subscription fee", "monthly fee", "annual fee", "discount",
            "coupon", "promo code", "pricing plan",
        ],
        "priority": "P2",
    },
    "legal": {
        "keywords": [
            "lawsuit", "lawyer", "attorney", "legal action", "sue", "court",
            "gdpr", "data protection", "data request", "privacy request",
            "delete my data", "right to be forgotten", "compliance",
            "regulation", "regulatory", "breach of contract",
        ],
        "priority": "P1",
    },
    "account_cancellation": {
        "keywords": [
            "cancel my account", "close my account", "delete my account",
            "cancel subscription", "terminate account", "unsubscribe",
            "i want to cancel", "cancel my plan",
        ],
        "priority": "P1",
    },
    "competitor": {
        "keywords": [
            # Generic competitor mentions are handled by LLM classifier
            # These are specific patterns we can detect
            "switch to", "switching to", "migrate to", "competitor",
            "better than you", "other company", "different provider",
        ],
        "priority": "P2",
    },
}

# Profanity keywords (from analyze_sentiment.py — duplicated for independence)
PROFANITY_KEYWORDS = [
    "fuck", "shit", "bitch", "asshole", "damn", "crap",
    "bastard", "idiot", "moron", "stupid",
]


def _keyword_check(text: str) -> Optional[tuple[str, str]]:
    """
    Fast keyword-based escalation check.
    Returns (trigger_rule, matched_keyword) or None.
    """
    text_lower = text.lower()

    # Profanity check first (highest priority)
    for keyword in PROFANITY_KEYWORDS:
        if keyword in text_lower:
            return ("profanity", keyword)

    # Domain-specific rules
    for rule_name, rule_config in ESCALATION_RULES.items():
        for keyword in rule_config["keywords"]:
            if keyword in text_lower:
                return (rule_name, keyword)

    return None


async def _llm_escalation_check(text: str) -> Optional[tuple[str, str, str]]:
    """
    Use GPT-4o to classify escalation for ambiguous cases.
    Returns (trigger_rule, trigger_detail, priority) or None if no escalation.
    """
    prompt = """You are a customer support escalation classifier. Analyze this customer message and determine if it requires human escalation.

ESCALATE if the message contains:
- Pricing inquiry (asking about costs, fees, discounts)
- Refund request (asking for money back, chargeback)
- Legal matter (lawsuit threat, GDPR request, compliance issue)
- Account cancellation request
- Mention of a competitor product by name

DO NOT ESCALATE for:
- Technical support questions
- How-to questions
- Feature requests
- General product inquiries

Respond with JSON only:
{
  "should_escalate": true/false,
  "trigger_rule": "pricing|refund|legal|competitor|account_cancellation|none",
  "trigger_detail": "specific phrase or reason",
  "priority": "P1|P2|P3"
}

Priority guide: P1=refund/legal/cancellation, P2=pricing/competitor, P3=unclear/other

Customer message: """ + f'"{text}"'

    try:
        response = await openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        import json
        result = json.loads(response.choices[0].message.content)

        if result.get("should_escalate") and result.get("trigger_rule") != "none":
            return (
                result.get("trigger_rule", "undocumented"),
                result.get("trigger_detail", text[:100]),
                result.get("priority", "P2"),
            )
        return None
    except Exception as e:
        logger.warning("LLM escalation check failed: %s", e)
        return None


async def decide_escalation(
    text: str,
    sentiment_score: Optional[float] = None,
    profanity_detected: bool = False,
) -> EscalationDecision:
    """
    Decide whether to escalate and why.

    Algorithm:
    1. Check sentiment threshold (score < 0.3 → escalate)
    2. Fast keyword check
    3. LLM classifier for ambiguous cases
    4. Return EscalationDecision

    Returns EscalationDecision(should_escalate=False) for normal messages.
    """
    # Step 1: Sentiment threshold
    if sentiment_score is not None and sentiment_score < 0.3:
        logger.info("Escalating: sentiment score %.3f < 0.3", sentiment_score)
        return EscalationDecision(
            should_escalate=True,
            trigger_rule="sentiment",
            trigger_detail=f"Sentiment score {sentiment_score:.3f} below threshold 0.3",
            priority="P1",
        )

    # Step 2: Profanity flag
    if profanity_detected:
        return EscalationDecision(
            should_escalate=True,
            trigger_rule="profanity",
            trigger_detail="Profanity detected in customer message",
            priority="P2",
        )

    # Step 3: Fast keyword check
    keyword_result = _keyword_check(text)
    if keyword_result:
        rule, matched = keyword_result
        priority = ESCALATION_RULES.get(rule, {}).get("priority", "P2")
        if rule == "profanity":
            priority = "P2"
        logger.info("Escalating via keyword rule '%s': matched '%s'", rule, matched)
        return EscalationDecision(
            should_escalate=True,
            trigger_rule=rule,
            trigger_detail=f"Keyword matched: '{matched}'",
            priority=priority,
        )

    # Step 4: LLM classifier for potentially ambiguous cases
    # Run LLM check if message mentions money, legal terms, or competitor patterns
    ambiguous_patterns = ["cost", "price", "fee", "competitor", "other service",
                          "gdpr", "data", "cancel", "terminate", "refund"]
    text_lower = text.lower()
    needs_llm_check = any(p in text_lower for p in ambiguous_patterns)

    if needs_llm_check:
        llm_result = await _llm_escalation_check(text)
        if llm_result:
            rule, detail, priority = llm_result
            logger.info("Escalating via LLM classifier: rule='%s'", rule)
            return EscalationDecision(
                should_escalate=True,
                trigger_rule=rule,
                trigger_detail=detail,
                priority=priority,
            )

    # No escalation triggered
    return EscalationDecision(
        should_escalate=False,
        trigger_rule=None,
        trigger_detail=None,
        priority="P3",
    )


class EscalationAgent:
    """
    OpenAI Agents SDK-compatible wrapper for escalation decision logic.
    Can be used as a standalone sub-agent or called inline from the orchestrator.
    """

    async def run(
        self,
        text: str,
        sentiment_score: Optional[float] = None,
        profanity_detected: bool = False,
    ) -> EscalationDecision:
        """Run the escalation decision logic."""
        return await decide_escalation(
            text=text,
            sentiment_score=sentiment_score,
            profanity_detected=profanity_detected,
        )
