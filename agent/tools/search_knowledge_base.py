"""
agent/tools/search_knowledge_base.py — KB semantic search tool wrapper.

Calls kb_repo.semantic_search with timeout handling.
Returns kb_miss=True on timeout (E001) without raising.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.kb_repo import KBResult, semantic_search

logger = logging.getLogger(__name__)

KB_SEARCH_TIMEOUT = 3.0  # seconds


@dataclass
class KBSearchResult:
    """Result of search_knowledge_base tool call."""
    results: list[KBResult]
    kb_miss: bool
    error: Optional[str] = None


async def search_knowledge_base(
    session: AsyncSession,
    query: str,
    threshold: float = 0.75,
    top_k: int = 5,
    ticket_id: Optional[uuid.UUID] = None,
    kafka_producer=None,
) -> KBSearchResult:
    """
    Search the knowledge base for articles matching the query.

    - Calls kb_repo.semantic_search (pgvector cosine similarity)
    - Handles timeout gracefully (E001): returns kb_miss=True, does not raise
    - Logs structured metric event

    Args:
        session: async database session
        query: customer question / message text
        threshold: minimum similarity score (0.0–1.0)
        top_k: maximum results to return
        ticket_id: current ticket ID for metric logging
        kafka_producer: Kafka producer for metrics (optional)

    Returns:
        KBSearchResult with results list and kb_miss flag
    """
    start_time = time.monotonic()

    try:
        results = await asyncio.wait_for(
            semantic_search(
                session=session,
                query_text=query,
                top_k=top_k,
                threshold=threshold,
            ),
            timeout=KB_SEARCH_TIMEOUT,
        )

        kb_miss = len(results) == 0
        duration_ms = int((time.monotonic() - start_time) * 1000)

        logger.info(
            '{"timestamp":"%s","ticket_id":"%s","tool_name":"search_knowledge_base",'
            '"input_hash":"%s","output_status":"success","duration_ms":%d,'
            '"channel":null,"result_count":%d}',
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            str(ticket_id) if ticket_id else "null",
            query[:16],
            duration_ms,
            len(results),
        )

        return KBSearchResult(results=results, kb_miss=kb_miss)

    except asyncio.TimeoutError:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.warning(
            '{"timestamp":"%s","ticket_id":"%s","tool_name":"search_knowledge_base",'
            '"output_status":"E001","duration_ms":%d,"error":"KB search timed out"}',
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            str(ticket_id) if ticket_id else "null",
            duration_ms,
        )
        return KBSearchResult(
            results=[],
            kb_miss=True,
            error="E001: KB search timed out — proceeding without KB context",
        )

    except Exception as e:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.error(
            '{"timestamp":"%s","ticket_id":"%s","tool_name":"search_knowledge_base",'
            '"output_status":"error","duration_ms":%d,"error":"%s"}',
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            str(ticket_id) if ticket_id else "null",
            duration_ms,
            str(e)[:100],
        )
        # Return kb_miss rather than raising — pipeline can continue without KB
        return KBSearchResult(
            results=[],
            kb_miss=True,
            error=f"KB search error: {str(e)[:100]}",
        )
