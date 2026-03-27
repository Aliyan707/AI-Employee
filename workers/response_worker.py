"""
workers/response_worker.py — Kafka consumer for cs.response topic.

Routes formatted responses to the correct channel sender:
  - email → channels/gmail/sender.send_gmail_reply
  - whatsapp → channels/whatsapp/sender.send_whatsapp
  - webform → updates messages.delivery_status to 'sent'
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from aiokafka import AIOKafkaConsumer

from config import get_settings
from database.session import get_db_context

logger = logging.getLogger(__name__)
settings = get_settings()

CONSUMER_GROUP = "response-worker"
TOPIC = "cs.response"


async def dispatch_response(response_event: dict) -> bool:
    """
    Route a response event to the appropriate channel sender.

    Returns True on success, False on failure (for retry logic).
    """
    channel = response_event.get("channel", "")
    response_text = response_event.get("response_text", "")
    ticket_id = response_event.get("ticket_id")
    channel_metadata = response_event.get("channel_metadata", {})
    customer_identifiers = response_event.get("customer_identifiers", {})

    if not response_text:
        logger.warning("Response event has empty response_text for ticket %s", ticket_id)
        return True  # Nothing to send, but not an error

    if channel == "whatsapp":
        phone = customer_identifiers.get("phone") or customer_identifiers.get("whatsapp_id")
        if phone:
            from channels.whatsapp.sender import send_whatsapp
            success = await send_whatsapp(to_number=phone, text=response_text)
            if success:
                logger.info("WhatsApp response sent for ticket %s", ticket_id)
            return success
        else:
            logger.error("No phone number for WhatsApp response (ticket=%s)", ticket_id)
            return False

    elif channel == "email":
        email_address = customer_identifiers.get("email")
        thread_id = channel_metadata.get("thread_id")
        subject = channel_metadata.get("subject", "Re: Support Request")

        if email_address and thread_id:
            from channels.gmail.sender import send_gmail_reply
            html_body = response_text.replace("\n", "<br>")
            success = await send_gmail_reply(
                thread_id=thread_id,
                to_address=email_address,
                subject=subject if subject.startswith("Re:") else f"Re: {subject}",
                html_body=html_body,
            )
            if success:
                logger.info("Email response sent for ticket %s", ticket_id)
            return success
        else:
            logger.error(
                "Missing email or thread_id for email response (ticket=%s)", ticket_id
            )
            return False

    elif channel == "webform":
        # Webform: update delivery_status in DB (client polls or SSE)
        if ticket_id:
            async with get_db_context() as db:
                from sqlalchemy import text
                await db.execute(
                    text("""
                        UPDATE messages
                        SET delivery_status = 'sent'
                        WHERE ticket_id = :ticket_id
                          AND direction = 'outbound'
                          AND delivery_status = 'pending'
                    """),
                    {"ticket_id": ticket_id},
                )
                await db.commit()
            logger.info("Webform delivery_status updated for ticket %s", ticket_id)
        return True

    else:
        logger.error("Unknown channel: %s (ticket=%s)", channel, ticket_id)
        return False


async def run_response_worker() -> None:
    """Main response worker loop."""
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=CONSUMER_GROUP,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda v: v,
    )

    await consumer.start()
    logger.info("Response worker started, consuming from %s", TOPIC)

    try:
        async for msg in consumer:
            try:
                response_event = json.loads(msg.value.decode("utf-8"))

                success = await dispatch_response(response_event)

                if not success:
                    # E001: retry once
                    logger.warning("Response dispatch failed, retrying once...")
                    await asyncio.sleep(1.0)
                    success = await dispatch_response(response_event)
                    if not success:
                        logger.error(
                            "Response dispatch failed after retry for ticket %s",
                            response_event.get("ticket_id"),
                        )
                        # TODO: dead-letter queue

                # Commit regardless of success (to avoid infinite retry loops)
                await consumer.commit()

            except Exception as e:
                logger.error("Error processing response message: %s", e)
                await consumer.commit()  # Commit to avoid blocking

    finally:
        await consumer.stop()
        logger.info("Response worker stopped")


def main():
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run_response_worker())


if __name__ == "__main__":
    main()
