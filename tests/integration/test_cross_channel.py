"""
tests/integration/test_cross_channel.py — Cross-channel identity resolution tests.

Tests that the same customer is identified across different channels
based on email/phone identifiers.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.repositories.customer_repo import (
    normalise_email,
    normalise_identifiers,
    normalise_phone,
)


class TestCrossChannelIdentityResolution:
    """Tests for cross-channel identity matching (pure function tests)."""

    def test_email_normalisation_consistent(self):
        """Same email in different cases should normalise identically."""
        email1 = normalise_email("User@Example.com")
        email2 = normalise_email("user@example.com")
        email3 = normalise_email("  USER@EXAMPLE.COM  ")
        assert email1 == email2 == email3 == "user@example.com"

    def test_phone_normalisation_consistent(self):
        """Same phone in different formats should normalise identically."""
        formats = [
            "+14155551234",
            "+1 415 555 1234",
            "+1 (415) 555-1234",
            "14155551234",
        ]
        normalised = [normalise_phone(f) for f in formats]
        # All should produce the same E.164 number
        assert all(n == "+14155551234" for n in normalised)

    def test_webform_identifiers_extracted(self):
        """Webform channel identifiers should include email."""
        identifiers = normalise_identifiers({
            "email": "customer@test.com",
        })
        assert identifiers["email"] == "customer@test.com"

    def test_whatsapp_identifiers_extracted(self):
        """WhatsApp channel should include phone and whatsapp_id."""
        identifiers = normalise_identifiers({
            "phone": "+14155551234",
            "whatsapp_id": "whatsapp:+14155551234",
        })
        assert identifiers["phone"] == "+14155551234"
        assert identifiers["whatsapp_id"] == "+14155551234"  # whatsapp: prefix stripped

    def test_email_identifies_same_customer_across_channels(self):
        """Same email submitted from different channels produces same normalised identifier."""
        webform_ids = normalise_identifiers({"email": "alice@example.com"})
        email_channel_ids = normalise_identifiers({"email": "ALICE@EXAMPLE.COM"})

        assert webform_ids["email"] == email_channel_ids["email"]

    def test_multiple_identifier_types_in_single_lookup(self):
        """Customer with email + phone should have both identifiers normalised."""
        identifiers = normalise_identifiers({
            "email": "Bob@Test.COM",
            "phone": "+1 (800) 555-0100",
        })
        assert "email" in identifiers
        assert "phone" in identifiers
        assert identifiers["email"] == "bob@test.com"
        assert identifiers["phone"].startswith("+")


class TestIntakeEventChannelIdentifiers:
    """Tests that different channel handlers produce compatible identifiers."""

    def test_webform_produces_email_identifier(self):
        """Web form handler should produce email identifier."""
        from channels.webform.handler import WebformPayload, normalise_webform

        payload = WebformPayload(
            email="Customer@Test.com",
            message="Hello",
        )
        event = normalise_webform(payload)

        assert "email" in event.customer_identifiers
        assert event.customer_identifiers["email"] == "customer@test.com"

    def test_whatsapp_produces_phone_identifier(self):
        """WhatsApp handler should produce phone identifier."""
        from channels.whatsapp.webhook import TwilioWebhookPayload, normalise_whatsapp

        payload = TwilioWebhookPayload(
            From="whatsapp:+14155551234",
            To="whatsapp:+14155238886",
            Body="Hello",
            MessageSid="SM123",
        )
        event = normalise_whatsapp(payload)

        assert "phone" in event.customer_identifiers
        assert event.customer_identifiers["phone"].startswith("+")
        assert event.channel == "whatsapp"
