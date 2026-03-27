"""
workers/metrics_worker.py — Kafka consumer for cs.metrics topic.

Batch-inserts agent_metrics rows every 5 seconds or 100 messages.
"""

import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from aiokafka import AIOKafkaConsumer

from config import get_settings
from database.session import get_db_context

logger = logging.getLogger(__name__)
settings = get_settings()

CONSUMER_GROUP = "metrics-worker"
TOPIC = "cs.metrics"
BATCH_SIZE = 100
FLUSH_INTERVAL = 5.0  # seconds


async def flush_metrics_batch(metrics_batch: list[dict]) -> int:
    """
    Batch-insert metrics events into agent_metrics table.
    Returns number of rows inserted.
    """
    if not metrics_batch:
        return 0

    async with get_db_context() as db:
        from sqlalchemy import text
        for event in metrics_batch:
            ticket_id = event.get("ticket_id")
            channel = event.get("channel")

            # Validate channel value
            if channel not in ("email", "whatsapp", "webform", None):
                channel = None

            await db.execute(
                text("""
                    INSERT INTO agent_metrics
                    (ticket_id, tool_name, channel, input_hash, output_status, duration_ms, error_code)
                    VALUES (:ticket_id, :tool_name, :channel, :input_hash, :output_status, :duration_ms, :error_code)
                """),
                {
                    "ticket_id": ticket_id,
                    "tool_name": event.get("tool_name", "unknown"),
                    "channel": channel,
                    "input_hash": event.get("input_hash"),
                    "output_status": event.get("output_status", "success"),
                    "duration_ms": event.get("duration_ms"),
                    "error_code": event.get("error_code"),
                },
            )
        await db.commit()
        logger.debug("Flushed %d metrics events to DB", len(metrics_batch))
        return len(metrics_batch)


async def run_metrics_worker() -> None:
    """Main metrics worker loop with batching."""
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda v: v,
    )

    await consumer.start()
    logger.info("Metrics worker started, consuming from %s", TOPIC)

    batch: list[dict] = []
    last_flush = asyncio.get_event_loop().time()

    try:
        async for msg in consumer:
            try:
                event = json.loads(msg.value.decode("utf-8"))
                batch.append(event)

                current_time = asyncio.get_event_loop().time()
                should_flush = (
                    len(batch) >= BATCH_SIZE
                    or (current_time - last_flush) >= FLUSH_INTERVAL
                )

                if should_flush:
                    inserted = await flush_metrics_batch(batch)
                    batch.clear()
                    last_flush = current_time
                    await consumer.commit()

            except Exception as e:
                logger.error("Error processing metrics message: %s", e)

    finally:
        # Flush remaining batch on shutdown
        if batch:
            await flush_metrics_batch(batch)
        await consumer.stop()
        logger.info("Metrics worker stopped")


def main():
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run_metrics_worker())


if __name__ == "__main__":
    main()
