"""
database/repositories/kb_repo.py — Knowledge base semantic search via pgvector.

Uses OpenAI text-embedding-3-small to embed queries, then performs
cosine similarity search against the HNSW-indexed knowledge_base table.
"""

import logging
from dataclasses import dataclass
from typing import Optional
import uuid

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


@dataclass
class KBResult:
    """A knowledge base search result with similarity score."""
    article_id: uuid.UUID
    title: str
    content: str
    score: float
    topic_tags: list[str]


async def embed_text(text_input: str) -> list[float]:
    """
    Generate an embedding vector for the given text using OpenAI API.
    Returns a list of 1536 floats.
    """
    response = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text_input,
        dimensions=EMBEDDING_DIMENSION,
    )
    return response.data[0].embedding


async def semantic_search(
    session: AsyncSession,
    query_text: str,
    top_k: int = 5,
    threshold: float = 0.75,
) -> list[KBResult]:
    """
    Search the knowledge base using cosine similarity.

    Steps:
    1. Embed the query text via OpenAI text-embedding-3-small
    2. Run pgvector cosine similarity query (1 - cosine_distance = cosine_similarity)
    3. Filter results by similarity threshold
    4. Return top_k results as KBResult objects

    Args:
        session: async database session
        query_text: the customer's question/message text
        top_k: maximum number of results to return
        threshold: minimum similarity score (0.0–1.0) to include

    Returns:
        List of KBResult sorted by similarity score descending
    """
    # Generate query embedding
    query_embedding = await embed_text(query_text)

    # Format embedding as PostgreSQL vector literal
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # pgvector cosine similarity: 1 - (embedding <=> query_vector)
    # <=> is the cosine distance operator; similarity = 1 - distance
    stmt = text("""
        SELECT
            id,
            title,
            content,
            topic_tags,
            1 - (embedding <=> :query_embedding::vector) AS similarity
        FROM knowledge_base
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> :query_embedding::vector
        LIMIT :top_k
    """)

    result = await session.execute(
        stmt,
        {
            "query_embedding": embedding_str,
            "top_k": top_k,
        },
    )

    rows = result.fetchall()

    # Filter by threshold and build result objects
    kb_results = []
    for row in rows:
        similarity = float(row[4]) if row[4] is not None else 0.0
        if similarity >= threshold:
            kb_results.append(
                KBResult(
                    article_id=row[0],
                    title=row[1],
                    content=row[2],
                    score=similarity,
                    topic_tags=row[3] or [],
                )
            )

    logger.debug(
        "KB search for '%s...': %d results (threshold %.2f)",
        query_text[:50],
        len(kb_results),
        threshold,
    )

    return kb_results


async def upsert_kb_article(
    session: AsyncSession,
    title: str,
    content: str,
    topic_tags: Optional[list[str]] = None,
    source_url: Optional[str] = None,
    article_id: Optional[uuid.UUID] = None,
) -> uuid.UUID:
    """
    Insert or update a knowledge base article with its embedding.
    Used by seed_kb.py and admin endpoints.
    """
    embedding = await embed_text(f"{title}\n\n{content}")
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    if article_id is None:
        article_id = uuid.uuid4()

    stmt = text("""
        INSERT INTO knowledge_base (id, title, content, topic_tags, embedding, source_url)
        VALUES (
            :id,
            :title,
            :content,
            :topic_tags,
            :embedding::vector,
            :source_url
        )
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            topic_tags = EXCLUDED.topic_tags,
            embedding = EXCLUDED.embedding,
            source_url = EXCLUDED.source_url,
            updated_at = NOW()
    """)

    await session.execute(
        stmt,
        {
            "id": str(article_id),
            "title": title,
            "content": content,
            "topic_tags": topic_tags or [],
            "embedding": embedding_str,
            "source_url": source_url,
        },
    )
    await session.commit()

    logger.info("Upserted KB article: %s (id=%s)", title, article_id)
    return article_id
