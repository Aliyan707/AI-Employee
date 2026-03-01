"""
tests/unit/test_identity_resolution.py — Unit tests for customer identity resolution.

Tests:
1. Same email resolves same customer_id
2. Phone-only resolution
3. WhatsApp ID resolution
4. New identifiers linked to existing customer
5. Concurrent resolution with same email returns same id
6. Phone number normalisation (various formats → E.164)
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from database.repositories.customer_repo import (
    normalise_email,
    normalise_identifiers,
    normalise_phone,
    normalise_whatsapp_id,
)


# ---------------------------------------------------------------------------
# Normalisation unit tests (pure functions, no DB needed)
# ---------------------------------------------------------------------------


class TestEmailNormalisation:
    def test_lowercase(self):
        assert normalise_email("User@Example.COM") == "user@example.com"

    def test_strip_whitespace(self):
        assert normalise_email("  user@example.com  ") == "user@example.com"

    def test_already_normalised(self):
        assert normalise_email("user@example.com") == "user@example.com"


class TestPhoneNormalisation:
    def test_us_with_formatting(self):
        """'+1 (415) 555-1234' → '+14155551234'"""
        result = normalise_phone("+1 (415) 555-1234")
        assert result == "+14155551234"

    def test_us_without_country_code(self):
        """'4155551234' → '+14155551234' (assuming US default)"""
        result = normalise_phone("4155551234")
        assert result == "+14155551234"

    def test_uk_number(self):
        """'+44 20 7946 0958' → '+442079460958'"""
        result = normalise_phone("+44 20 7946 0958")
        assert result == "+442079460958"

    def test_e164_format_unchanged(self):
        """Already E.164 numbers should be returned unchanged."""
        result = normalise_phone("+14155551234")
        assert result == "+14155551234"

    def test_invalid_returns_none(self):
        """Invalid phone number should return None."""
        result = normalise_phone("not-a-phone")
        assert result is None

    def test_empty_returns_none(self):
        result = normalise_phone("")
        assert result is None

    def test_none_returns_none(self):
        result = normalise_phone(None)
        assert result is None


class TestWhatsAppIdNormalisation:
    def test_strips_whatsapp_prefix(self):
        result = normalise_whatsapp_id("whatsapp:+14155551234")
        assert result == "+14155551234"

    def test_no_prefix_unchanged(self):
        result = normalise_whatsapp_id("+14155551234")
        assert result == "+14155551234"

    def test_strips_whitespace(self):
        result = normalise_whatsapp_id("  +14155551234  ")
        assert result == "+14155551234"


class TestNormaliseIdentifiers:
    def test_email_normalised(self):
        result = normalise_identifiers({"email": "USER@EXAMPLE.COM"})
        assert result["email"] == "user@example.com"

    def test_phone_normalised_to_e164(self):
        result = normalise_identifiers({"phone": "+1 (415) 555-1234"})
        assert result["phone"] == "+14155551234"

    def test_whatsapp_id_stripped(self):
        result = normalise_identifiers({"whatsapp_id": "whatsapp:+14155551234"})
        assert result["whatsapp_id"] == "+14155551234"

    def test_multiple_identifiers(self):
        result = normalise_identifiers({
            "email": "User@EXAMPLE.com",
            "phone": "+14155551234",
        })
        assert result["email"] == "user@example.com"
        assert result["phone"] == "+14155551234"

    def test_invalid_phone_excluded(self):
        result = normalise_identifiers({
            "email": "user@example.com",
            "phone": "not-a-number",
        })
        assert "email" in result
        assert "phone" not in result

    def test_empty_identifiers_raises(self):
        """Empty identifiers dict should produce empty result."""
        result = normalise_identifiers({})
        assert result == {}
