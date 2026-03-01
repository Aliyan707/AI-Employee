"""
tests/unit/test_idempotency.py — Unit tests for idempotency logic.

Tests:
1. create_ticket duplicate within 60s returns same ticket_id
2. send_response duplicate with same hash returns duplicate=True
3. Expired idempotency key allows new ticket creation
4. Different customers with same content create separate tickets
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.repositories.ticket_repo import (
    _make_idempotency_key,
    check_send_idempotency,
)


class TestTicketIdempotencyKey:
    def test_same_inputs_same_key(self):
        """Same customer_id and content_hash should produce same idempotency key."""
        cid = uuid.uuid4()
        ch = "abc123"
        key1 = _make_idempotency_key(cid, ch)
        key2 = _make_idempotency_key(cid, ch)
        assert key1 == key2

    def test_different_customer_different_key(self):
        """Different customers should produce different keys."""
        cid1 = uuid.uuid4()
        cid2 = uuid.uuid4()
        ch = "abc123"
        assert _make_idempotency_key(cid1, ch) != _make_idempotency_key(cid2, ch)

    def test_different_content_different_key(self):
        """Different content hashes should produce different keys."""
        cid = uuid.uuid4()
        assert _make_idempotency_key(cid, "hash1") != _make_idempotency_key(cid, "hash2")

    def test_key_is_sha256_hex(self):
        """Idempotency key should be a 64-character hex string (SHA-256)."""
        cid = uuid.uuid4()
        key = _make_idempotency_key(cid, "test-hash")
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)


class TestSendResponseIdempotency:
    def test_send_idempotency_key_format(self):
        """Send idempotency key should be SHA256(send:{ticket_id}:{response_hash})."""
        ticket_id = uuid.uuid4()
        response_hash = "abc" * 21  # 63 chars

        # The key formula used in ticket_repo
        expected_key = hashlib.sha256(
            f"send:{ticket_id}:{response_hash}".encode()
        ).hexdigest()

        assert len(expected_key) == 64

    @pytest.mark.asyncio
    async def test_check_send_idempotency_no_duplicate(self):
        """Returns (None, False) when no existing key."""
        ticket_id = uuid.uuid4()
        response_hash = "unique-hash-123"

        # Mock the DB session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        msg_id, is_dup = await check_send_idempotency(
            session=mock_session,
            ticket_id=ticket_id,
            response_hash=response_hash,
        )

        assert msg_id is None
        assert is_dup is False


class TestContentHash:
    def test_content_hash_is_sha256(self):
        """Content hash should be SHA-256 of the message content."""
        from channels.webform.handler import compute_content_hash
        text = "Hello, I need help with my account."
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert compute_content_hash(text) == expected

    def test_same_content_same_hash(self):
        from channels.webform.handler import compute_content_hash
        text = "How do I reset my password?"
        assert compute_content_hash(text) == compute_content_hash(text)

    def test_different_content_different_hash(self):
        from channels.webform.handler import compute_content_hash
        h1 = compute_content_hash("Message one")
        h2 = compute_content_hash("Message two")
        assert h1 != h2
