"""
workers/kafka_client.py — Shared Kafka producer/consumer utilities.

Provides:
  - KafkaProducer singleton with JSON serialisation
  - create_topics(): create the 4 required topics idempotently
  - get_kafka_producer(): FastAPI dependency
  - close_kafka_producer(): shutdown cleanup
"""

import asyncio
import json
import logging
from typing import Optional

from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Topic configurations
KAFKA_TOPICS = [
    NewTopic(
        name="cs.intake",
        num_partitions=3,
        replication_factor=1,
        topic_configs={"retention.ms": str(7 * 24 * 60 * 60 * 1000)},  # 7 days
    ),
    NewTopic(
        name="cs.response",
        num_partitions=3,
        replication_factor=1,
        topic_configs={"retention.ms": str(7 * 24 * 60 * 60 * 1000)},
    ),
    NewTopic(
        name="cs.escalation",
        num_partitions=1,
        replication_factor=1,
        topic_configs={"retention.ms": str(30 * 24 * 60 * 60 * 1000)},  # 30 days
    ),
    NewTopic(
        name="cs.metrics",
        num_partitions=2,
        replication_factor=1,
        topic_configs={"retention.ms": str(7 * 24 * 60 * 60 * 1000)},
    ),
]

# Singleton producer
_kafka_producer: Optional[AIOKafkaProducer] = None
_producer_lock = asyncio.Lock()


async def create_topics() -> None:
    """
    Create required Kafka topics idempotently.
    Ignores errors if topics already exist.
    """
    try:
        admin = AIOKafkaAdminClient(
            bootstrap_servers=settings.kafka_bootstrap_servers,
        )
        await admin.start()
        try:
            existing = await admin.list_topics()
            topics_to_create = [
                t for t in KAFKA_TOPICS if t.name not in existing
            ]
            if topics_to_create:
                await admin.create_topics(topics_to_create)
                logger.info(
                    "Created Kafka topics: %s",
                    [t.name for t in topics_to_create],
                )
            else:
                logger.debug("All Kafka topics already exist")
        finally:
            await admin.close()
    except Exception as e:
        logger.warning("Failed to create Kafka topics: %s", e)


async def get_kafka_producer() -> Optional[AIOKafkaProducer]:
    """
    Get or create the shared Kafka producer singleton.
    Returns None if Kafka is unavailable (graceful degradation).
    """
    global _kafka_producer

    async with _producer_lock:
        if _kafka_producer is not None:
            return _kafka_producer

        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: v if isinstance(v, bytes) else json.dumps(v).encode("utf-8"),
                acks="all",
                compression_type="gzip",
                max_batch_size=16384,
                linger_ms=5,
            )
            await producer.start()
            _kafka_producer = producer
            logger.info(
                "Kafka producer connected to %s", settings.kafka_bootstrap_servers
            )
            return _kafka_producer
        except Exception as e:
            logger.warning("Kafka producer initialization failed: %s", e)
            return None


async def close_kafka_producer() -> None:
    """Close the shared Kafka producer on shutdown."""
    global _kafka_producer

    if _kafka_producer:
        try:
            await _kafka_producer.stop()
            logger.info("Kafka producer closed")
        except Exception as e:
            logger.warning("Error closing Kafka producer: %s", e)
        finally:
            _kafka_producer = None
