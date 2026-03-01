"""
channels/gmail/reader.py — Gmail PubSub push notification decoder.

decode_gmail_push(pubsub_data: str) -> IntakeEvent
  - Decodes base64 PubSub message
  - Fetches full Gmail message via Gmail API
  - Extracts from_address, thread_id, subject, body
  - Sets channel="email"
"""

import base64
import email
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from channels.webform.handler import (
    ChannelMetadata,
    IntakeEvent,
    compute_content_hash,
)
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_gmail_service():
    """
    Build and return an authenticated Gmail API service.
    Uses service account credentials from GMAIL_CREDENTIALS_PATH.
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            settings.gmail_credentials_path,
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        )
        service = build("gmail", "v1", credentials=credentials)
        return service
    except Exception as e:
        logger.error("Failed to build Gmail service: %s", e)
        raise


def _extract_plain_text(msg_payload: dict) -> str:
    """
    Extract plain text body from Gmail message payload.
    Handles multipart messages and base64url encoding.
    """
    def _decode_body(body_data: str) -> str:
        # Gmail uses base64url encoding
        padded = body_data + "=" * (4 - len(body_data) % 4)
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")

    mime_type = msg_payload.get("mimeType", "")

    if mime_type == "text/plain":
        body_data = msg_payload.get("body", {}).get("data", "")
        if body_data:
            return _decode_body(body_data)

    elif mime_type.startswith("multipart/"):
        parts = msg_payload.get("parts", [])
        for part in parts:
            text = _extract_plain_text(part)
            if text:
                return text

    return ""


def _extract_header(headers: list, name: str) -> Optional[str]:
    """Extract a header value by name from Gmail message headers."""
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return None


async def decode_gmail_push(pubsub_data: str) -> IntakeEvent:
    """
    Decode a Gmail PubSub push notification into an IntakeEvent.

    The PubSub data is base64-encoded JSON:
    {"emailAddress": "...", "historyId": "12345"}

    Steps:
    1. Decode base64 PubSub data
    2. Fetch Gmail message history to find new messages
    3. Fetch full message content
    4. Extract from, subject, body, thread_id
    5. Return IntakeEvent(channel="email")
    """
    # Step 1: Decode PubSub data
    try:
        padded = pubsub_data + "=" * (4 - len(pubsub_data) % 4)
        decoded = base64.b64decode(padded).decode("utf-8")
        push_data = json.loads(decoded)
    except Exception as e:
        raise ValueError(f"Failed to decode PubSub data: {e}")

    email_address = push_data.get("emailAddress", "")
    history_id = push_data.get("historyId")

    if not history_id:
        raise ValueError("PubSub data missing historyId")

    # Step 2: Fetch new messages from Gmail API
    service = _get_gmail_service()

    try:
        history_response = service.users().history().list(
            userId="me",
            startHistoryId=str(int(history_id) - 1),
            historyTypes=["messageAdded"],
        ).execute()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Gmail history: {e}")

    history_items = history_response.get("history", [])
    if not history_items:
        raise ValueError("No new messages found in Gmail history")

    # Get the first new message
    message_id = None
    for item in history_items:
        messages = item.get("messagesAdded", [])
        if messages:
            message_id = messages[0]["message"]["id"]
            break

    if not message_id:
        raise ValueError("Could not find message ID in history")

    # Step 3: Fetch full message
    try:
        full_message = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Gmail message {message_id}: {e}")

    # Step 4: Extract fields
    payload = full_message.get("payload", {})
    headers = payload.get("headers", [])
    thread_id = full_message.get("threadId", message_id)

    from_header = _extract_header(headers, "From") or email_address
    subject = _extract_header(headers, "Subject") or "Support Request"

    # Parse from_address from "Name <email>" format
    if "<" in from_header and ">" in from_header:
        from_address = from_header.split("<")[1].rstrip(">").strip()
    else:
        from_address = from_header.strip()

    body = _extract_plain_text(payload) or full_message.get("snippet", "")

    if not body:
        raise ValueError("Could not extract message body")

    # Clean up quoted text (common email forwarding artifacts)
    lines = body.split("\n")
    clean_lines = []
    for line in lines:
        # Stop at typical reply markers
        if line.strip().startswith("On ") and " wrote:" in line:
            break
        if line.strip().startswith(">"):
            break
        clean_lines.append(line)
    body = "\n".join(clean_lines).strip()

    raw_content = body
    content_hash = compute_content_hash(raw_content)

    return IntakeEvent(
        schema_version="1.0",
        event_type="customer_inquiry",
        event_id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        session_id=thread_id,
        channel="email",
        raw_content=raw_content,
        content_hash=content_hash,
        customer_identifiers={"email": from_address.lower()},
        customer_name=None,
        channel_metadata=ChannelMetadata(
            thread_id=thread_id,
            subject=subject,
        ),
    )
