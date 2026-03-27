"""
agent/tools/analyze_sentiment.py — Sentiment analysis with profanity pre-check.

Fast profanity keyword check before LLM call.
Returns SentimentResult with score, label, profanity_detected, and escalate flag.
"""

import logging
import time
import uuid
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

# Profanity keyword list for fast pre-check (before LLM call)
PROFANITY_KEYWORDS = [
    "fuck",
    "shit",
    "bitch",
    "asshole",
    "damn",
    "crap",
    "bastard",
    "idiot",
    "moron",
    "stupid",
    "hate",
    "wtf",
]

SENTIMENT_LABELS = {
    (0.0, 0.3): "angry",
    (0.3, 0.5): "negative",
    (0.5, 0.7): "neutral",
    (0.7, 1.01): "positive",
}


@dataclass
class SentimentResult:
    """Result of analyze_sentiment tool call."""
    score: float                    # 0.0 (very negative) to 1.0 (very positive)
    label: str                      # angry | negative | neutral | positive
    profanity_detected: bool
    escalate: bool                  # True if score < 0.3 OR profanity_detected


def _get_label(score: float) -> str:
    """Map numeric score to sentiment label."""
    for (low, high), label in SENTIMENT_LABELS.items():
        if low <= score < high:
            return label
    return "neutral"


def _check_profanity(text: str) -> bool:
    """
    Fast profanity pre-check using keyword list.
    Returns True if any profanity keyword found in lowercase text.
    """
    text_lower = text.lower()
    for keyword in PROFANITY_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


async def analyze_sentiment(
    text: str,
    ticket_id: Optional[uuid.UUID] = None,
    kafka_producer=None,
) -> SentimentResult:
    """
    Analyze customer message sentiment.

    Algorithm:
    1. Fast profanity keyword pre-check (no LLM needed)
    2. If profanity detected: flag for escalation, still run LLM for score
    3. Call GPT-4o with structured prompt for 0.0–1.0 score
    4. Return SentimentResult(score, label, profanity_detected, escalate)

    escalate=True if: score < 0.3 OR profanity_detected

    Error handling: On LLM failure, return neutral score (0.5) — safe default.
    """
    start_time = time.monotonic()

    # Step 1: Fast profanity check
    profanity_detected = _check_profanity(text)

    if profanity_detected:
        logger.info(
            '{"timestamp":"%s","ticket_id":"%s","tool_name":"analyze_sentiment",'
            '"event":"profanity_detected"}',
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            str(ticket_id) if ticket_id else "null",
        )

    # Step 2: LLM sentiment analysis
    try:
        score = await _llm_sentiment_score(text)
    except Exception as e:
        logger.warning("Sentiment LLM failed, defaulting to neutral: %s", e)
        score = 0.5  # Safe neutral default

    # Step 3: Derive label and escalation flag
    label = _get_label(score)
    escalate = score < 0.3 or profanity_detected

    duration_ms = int((time.monotonic() - start_time) * 1000)

    logger.info(
        '{"timestamp":"%s","ticket_id":"%s","tool_name":"analyze_sentiment",'
        '"input_hash":"%s","output_status":"success","duration_ms":%d,'
        '"channel":null,"score":%.3f,"label":"%s","escalate":%s}',
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        str(ticket_id) if ticket_id else "null",
        text[:16],
        duration_ms,
        score,
        label,
        str(escalate).lower(),
    )

    return SentimentResult(
        score=score,
        label=label,
        profanity_detected=profanity_detected,
        escalate=escalate,
    )


async def _llm_sentiment_score(text: str) -> float:
    """
    Use GPT-4o to score sentiment from 0.0 to 1.0.

    Prompt instructs the model to return ONLY a float, no explanation.
    """
    prompt = f"""Rate the sentiment of this customer support message on a scale from 0.0 to 1.0.

0.0 = extremely angry, hostile, or distressed
0.3 = frustrated or unhappy
0.5 = neutral
0.7 = satisfied or positive
1.0 = very happy and appreciative

Respond with ONLY a number between 0.0 and 1.0 and nothing else.

Customer message: "{text}"

Sentiment score:"""

    response = await openai_client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=10,
    )

    raw = response.choices[0].message.content.strip()

    # Parse the float response
    try:
        score = float(raw)
        # Clamp to valid range
        return max(0.0, min(1.0, score))
    except (ValueError, TypeError):
        logger.warning("Could not parse sentiment score: '%s'", raw)
        return 0.5  # Default to neutral
