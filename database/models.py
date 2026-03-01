"""
database/models.py — SQLAlchemy 2.0 async ORM models for all 8 tables.

Uses mapped_column and Mapped[T] typed annotations as per SQLAlchemy 2.0 style.
Relationships: customer -> tickets, ticket -> messages, ticket -> escalation_record.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    primary_email: Mapped[Optional[str]] = mapped_column(String(320), unique=True)
    primary_phone: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    identifiers: Mapped[List["CustomerIdentifier"]] = relationship(
        "CustomerIdentifier", back_populates="customer", cascade="all, delete-orphan"
    )
    tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket", back_populates="customer"
    )


class CustomerIdentifier(Base):
    __tablename__ = "customer_identifiers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    identifier_type: Mapped[str] = mapped_column(
        Enum(
            "email",
            "phone",
            "whatsapp_id",
            "web_session",
            name="identifier_type",
            create_type=False,
        ),
        nullable=False,
    )
    identifier_value: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="identifiers"
    )


# ---------------------------------------------------------------------------
# Tickets, Messages, Escalation Records
# ---------------------------------------------------------------------------


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        Enum("email", "whatsapp", "webform", name="channel_type", create_type=False),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "open",
            "escalated",
            "pending_human",
            "resolved",
            "closed",
            name="ticket_status",
            create_type=False,
        ),
        nullable=False,
        server_default="open",
    )
    priority: Mapped[Optional[str]] = mapped_column(
        Enum("P1", "P2", "P3", name="ticket_priority", create_type=False),
        server_default="P3",
    )
    subject: Mapped[Optional[str]] = mapped_column(Text)
    escalated: Mapped[bool] = mapped_column(Boolean, server_default="false")
    escalation_reason: Mapped[Optional[str]] = mapped_column(Text)
    parent_ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id")
    )
    kb_article_ids: Mapped[Optional[List[uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True))
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="tickets")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="ticket", cascade="all, delete-orphan",
        order_by="Message.sent_at"
    )
    escalation_record: Mapped[Optional["EscalationRecord"]] = relationship(
        "EscalationRecord", back_populates="ticket", uselist=False
    )
    sub_tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket", foreign_keys=[parent_ticket_id]
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(
        Enum("inbound", "outbound", name="message_direction", create_type=False),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        Enum("email", "whatsapp", "webform", name="channel_type", create_type=False),
        nullable=False,
    )
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3))
    agent_decision: Mapped[Optional[dict]] = mapped_column(JSONB)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    delivery_status: Mapped[str] = mapped_column(
        String(32), server_default="pending"
    )

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="messages")


class EscalationRecord(Base):
    __tablename__ = "escalation_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id"),
        nullable=False,
        unique=True,
    )
    trigger_rule: Mapped[str] = mapped_column(String(64), nullable=False)
    trigger_detail: Mapped[Optional[str]] = mapped_column(Text)
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3))
    priority: Mapped[str] = mapped_column(
        Enum("P1", "P2", "P3", name="ticket_priority", create_type=False),
        nullable=False,
    )
    assigned_agent: Mapped[Optional[str]] = mapped_column(String(255))
    resolved: Mapped[bool] = mapped_column(Boolean, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    ticket: Mapped["Ticket"] = relationship(
        "Ticket", back_populates="escalation_record"
    )


# ---------------------------------------------------------------------------
# Knowledge Base
# ---------------------------------------------------------------------------


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    topic_tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536))
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# Agent Metrics
# ---------------------------------------------------------------------------


class AgentMetric(Base):
    __tablename__ = "agent_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id")
    )
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[Optional[str]] = mapped_column(
        Enum("email", "whatsapp", "webform", name="channel_type", create_type=False)
    )
    input_hash: Mapped[Optional[str]] = mapped_column(String(64))
    output_status: Mapped[str] = mapped_column(String(16), nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    error_code: Mapped[Optional[str]] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Daily Reports
# ---------------------------------------------------------------------------


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    report_date: Mapped[datetime.date] = mapped_column(Date, nullable=False, unique=True)
    total_tickets: Mapped[int] = mapped_column(Integer, server_default="0")
    tickets_by_channel: Mapped[Optional[dict]] = mapped_column(JSONB)
    top_topics: Mapped[Optional[list]] = mapped_column(JSONB)
    mean_sentiment: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3))
    escalation_count: Mapped[int] = mapped_column(Integer, server_default="0")
    escalation_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Idempotency Keys
# ---------------------------------------------------------------------------


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
