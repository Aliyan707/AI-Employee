"""
agent/sub_agents/sentiment_agent.py — Sentiment analysis sub-agent.

Wraps analyze_sentiment tool as an OpenAI Agents SDK sub-agent.
Independently callable for testing and composition.
"""

import logging
import uuid
from typing import Optional

from agent.tools.analyze_sentiment import SentimentResult, analyze_sentiment

logger = logging.getLogger(__name__)


class SentimentAgent:
    """
    Dedicated sub-agent for sentiment analysis.
    Wraps the analyze_sentiment tool for use in the pipeline.

    Can be called independently or as part of the orchestrator's step 4.
    """

    async def run(
        self,
        text: str,
        ticket_id: Optional[uuid.UUID] = None,
        kafka_producer=None,
    ) -> SentimentResult:
        """
        Run sentiment analysis on the given text.

        Args:
            text: customer message to analyze
            ticket_id: optional ticket ID for metric logging
            kafka_producer: optional Kafka producer for metrics

        Returns:
            SentimentResult(score, label, profanity_detected, escalate)
        """
        logger.debug("SentimentAgent.run: analyzing message (len=%d)", len(text))

        result = await analyze_sentiment(
            text=text,
            ticket_id=ticket_id,
            kafka_producer=kafka_producer,
        )

        logger.debug(
            "SentimentAgent.run: score=%.3f, label=%s, escalate=%s",
            result.score,
            result.label,
            result.escalate,
        )

        return result
