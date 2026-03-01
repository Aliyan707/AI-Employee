"""
agent/sub_agents/kb_agent.py — Knowledge base search sub-agent.

Wraps search_knowledge_base tool as an OpenAI Agents SDK sub-agent.
Handles kb_miss gracefully without raising exceptions.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from agent.tools.search_knowledge_base import KBSearchResult, search_knowledge_base

logger = logging.getLogger(__name__)


class KBAgent:
    """
    Dedicated sub-agent for knowledge base search.
    Wraps the search_knowledge_base tool.

    Returns empty results (kb_miss=True) on timeout or no match — never raises.
    Can be used independently or as part of the orchestrator's step 3.
    """

    def __init__(self, threshold: float = 0.75, top_k: int = 5):
        self.threshold = threshold
        self.top_k = top_k

    async def run(
        self,
        query: str,
        session: AsyncSession,
        ticket_id: Optional[uuid.UUID] = None,
        kafka_producer=None,
    ) -> KBSearchResult:
        """
        Search the knowledge base for articles matching the query.

        Args:
            query: customer's message or question text
            session: async database session
            ticket_id: optional ticket ID for metric logging
            kafka_producer: optional Kafka producer for metrics

        Returns:
            KBSearchResult(results, kb_miss)
            kb_miss=True if no results above threshold or on error
        """
        logger.debug("KBAgent.run: searching for '%s...'", query[:50])

        result = await search_knowledge_base(
            session=session,
            query=query,
            threshold=self.threshold,
            top_k=self.top_k,
            ticket_id=ticket_id,
            kafka_producer=kafka_producer,
        )

        if result.kb_miss:
            logger.debug("KBAgent.run: kb_miss=True (no results above threshold)")
        else:
            logger.debug(
                "KBAgent.run: found %d results (top score=%.3f)",
                len(result.results),
                result.results[0].score if result.results else 0.0,
            )

        return result
