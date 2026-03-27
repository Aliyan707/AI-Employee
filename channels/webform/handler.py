"""
channels/webform/handler.py — Web form channel handler.

Normalises web form submissions into the common IntakeEvent schema.
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Pydantic model for incoming web form POST body
# ---------------------------------------------------------------------------


class WebformPayload(BaseModel):
    """
    Validated web form submission payload.
    email is required; name and phone are optional.
    """
    email: EmailStr = Field(..., description="Customer's email address (required)")
    name: Optional[str] = Field(None, description="Customer's display name (optional)")
    phone: Optional[str] = Field(None, description="Customer's phone number (optional)")
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Customer's message or question (required)",
    )
    subject: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional subject line",
    )

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or whitespace only")
        return stripped

    @field_validator("name")
    @classmethod
    def name_strip(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip() or None
        return None


# ---------------------------------------------------------------------------
# Common internal event schema (matches cs.intake Kafka topic format)
# ---------------------------------------------------------------------------


@dataclass
class ChannelMetadata:
    """Channel-specific metadata attached to an IntakeEvent."""
    form_source: Optional[str] = None       # webform
    thread_id: Optional[str] = None         # Gmail thread ID
    message_sid: Optional[str] = None       # Twilio message SID
    subject: Optional[str] = None           # Email subject


@dataclass
class IntakeEvent:
    """
    Normalised internal event representing an inbound customer inquiry.
    Created by channel handlers, consumed by OrchestratorAgent.
    """
    # Event identity
    schema_version: str
    event_type: str                         # "customer_inquiry"
    event_id: uuid.UUID
    timestamp: datetime
    session_id: str

    # Channel
    channel: str                            # email | whatsapp | webform

    # Content
    raw_content: str
    content_hash: str                       # SHA-256 of raw_content

    # Customer identifiers (for cross-channel resolution)
    customer_identifiers: dict              # {"email": ..., "phone": ..., etc.}
    customer_name: Optional[str]

    # Channel-specific metadata
    channel_metadata: ChannelMetadata = field(default_factory=ChannelMetadata)

    # Populated after resolution
    customer_id: Optional[uuid.UUID] = None
    ticket_id: Optional[uuid.UUID] = None


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content string for idempotency."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def normalise_webform(payload: WebformPayload) -> IntakeEvent:
    """
    Convert a validated WebformPayload into a normalised IntakeEvent.

    Computes content_hash for idempotency.
    Sets channel="webform" and extracts customer identifiers.
    """
    raw_content = payload.message.strip()
    content_hash = compute_content_hash(raw_content)

    # Build customer identifiers dict
    customer_identifiers: dict = {}
    if payload.email:
        customer_identifiers["email"] = payload.email.lower()
    if payload.phone:
        customer_identifiers["phone"] = payload.phone

    return IntakeEvent(
        schema_version="1.0",
        event_type="customer_inquiry",
        event_id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        session_id=str(uuid.uuid4()),
        channel="webform",
        raw_content=raw_content,
        content_hash=content_hash,
        customer_identifiers=customer_identifiers,
        customer_name=payload.name,
        channel_metadata=ChannelMetadata(
            form_source="webform",
            subject=payload.subject,
        ),
    )
