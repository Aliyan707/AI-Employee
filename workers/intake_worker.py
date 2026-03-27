"""
workers/intake_worker.py — Kafka consumer for cs.intake topic.

Consumes IntakeEvents, runs OrchestratorAgent pipeline,
and publishes response events to cs.response topic.
"""

import asyncio
import json
import logging
import signal
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from sqlalchemy.ext.asyncio import AsyncSession

from agent.orchestrator import OrchestratorAgent
from channels.webform.handler import ChannelMetadata, IntakeEvent
from config import get_settings
from database.repositories.customer_repo import resolve_or_create_customer
from database.session import get_db_context
from workers.kafka_client import get_kafka_producer

logger = logging.getLogger(__name__)
settings = get_settings()

CONSUMER_GROUP = "intake-worker"
TOPIC = "cs.intake"


def deserialise_intake_event(data: bytes) -> IntakeEvent:
    """Deserialise JSON bytes into an IntakeEvent."""
    raw = json.loads(data.decode("utf-8"))

    channel_meta_raw = raw.get("channel_metadata", {}) or {}
    channel_metadata = ChannelMetadata(
        form_source=channel_meta_raw.get("form_source"),
        thread_id=channel_meta_raw.get("thread_id"),
        message_sid=channel_meta_raw.get("message_sid"),
        subject=channel_meta_raw.get("subject"),
    )

    customer_id = None
    if raw.get("customer_id"):
        customer_id = uuid.UUID(raw["customer_id"])

    ticket_id = None
    if raw.get("ticket_id"):
        ticket_id = uuid.UUID(raw["ticket_id"])

    return IntakeEvent(
        schema_version=raw.get("schema_version", "1.0"),
        event_type=raw.get("event_type", "customer_inquiry"),
        event_id=uuid.UUID(raw["event_id"]) if raw.get("event_id") else uuid.uuid4(),
        timestamp=datetime.fromisoformat(raw["timestamp"]) if raw.get("timestamp") else datetime.now(timezone.utc),
        session_id=raw.get("session_id", str(uuid.uuid4())),
        channel=raw["channel"],
        raw_content=raw["raw_content"],
        content_hash=raw["content_hash"],
        customer_identifiers=raw.get("customer_identifiers", {}),
        customer_name=raw.get("customer_name"),
        channel_metadata=channel_metadata,
        customer_id=customer_id,
        ticket_id=ticket_id,
    )


async def process_intake_message(
    intake_event: IntakeEvent,
    db: AsyncSession,
    kafka_producer,
    orchestrator: OrchestratorAgent,
) -> None:
    """
    Process a single intake event through the pipeline.

    On success: publishes response to cs.response.
    On failure: logs to dead-letter.
    """
    # Resolve customer
    if not intake_event.customer_id:
        customer_id, _ = await resolve_or_create_customer(
            session=db,
            identifiers=intake_event.customer_identifiers,
            display_name=intake_event.customer_name,
        )
        intake_event.customer_id = customer_id

    # Run pipeline
    result = await orchestrator.run(
        session=db,
        intake_event=intake_event,
        kafka_producer=kafka_producer,
    )

    if result.response_text and kafka_producer:
        # Publish response to cs.response
        response_event = {
            "ticket_id": str(result.ticket_id) if result.ticket_id else None,
            "customer_id": str(result.customer_id) if result.customer_id else None,
            "channel": result.channel,
            "response_text": result.response_text,
            "escalated": result.escalated,
            "customer_identifiers": intake_event.customer_identifiers,
            "channel_metadata": {
                "thread_id": intake_event.channel_metadata.thread_id,
                "message_sid": intake_event.channel_metadata.message_sid,
                "subject": intake_event.channel_metadata.subject,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await kafka_producer.send(
            "cs.response",
            value=json.dumps(response_event).encode("utf-8"),
        )
        logger.info(
            "Response published to cs.response for ticket %s",
            result.ticket_id,
        )


async def run_intake_worker() -> None:
    """
    Main intake worker loop.
    Consumes cs.intake, processes messages, commits offsets.
    """
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,  # Manual commit for exactly-once semantics
        value_deserializer=lambda v: v,
    )

    orchestrator = OrchestratorAgent()
    kafka_producer = await get_kafka_producer()

    await consumer.start()
    logger.info("Intake worker started, consuming from %s", TOPIC)

    try:
        async for msg in consumer:
            try:
                intake_event = deserialise_intake_event(msg.value)
                logger.info(
                    "Processing intake message: channel=%s, session=%s",
                    intake_event.channel,
                    intake_event.session_id,
                )

                async with get_db_context() as db:
                    await process_intake_message(
                        intake_event=intake_event,
                        db=db,
                        kafka_producer=kafka_producer,
                        orchestrator=orchestrator,
                    )

                # Commit offset only after successful processing
                await consumer.commit()

            except Exception as e:
                logger.error(
                    "Failed to process intake message (offset=%s): %s",
                    msg.offset,
                    e,
                )
                # Don't commit — message will be redelivered
                # In production: publish to dead-letter topic after N retries

    finally:
        await consumer.stop()
        logger.info("Intake worker stopped")


def main():
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run_intake_worker())


if __name__ == "__main__":
    main()
