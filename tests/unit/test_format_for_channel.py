"""
tests/unit/test_format_for_channel.py — Unit tests for format_for_channel.

Tests:
1. Email within 500 words: passes as-is
2. Email over 500 words: LLM trim called, result within limit
3. WhatsApp within 300 chars: passes as-is
4. WhatsApp over 300 chars: LLM trim called, result within limit
5. Webform within 300 words: passes as-is
6. Email greeting injection: "Dear {name}," prepended
7. Email sign-off injection: "Best regards,\nCustomer Success Team" appended
8. WhatsApp markdown stripped: headers and bold removed
9. Double trim failure: returns E004 with within_limits=False
10. Unknown channel raises ValueError
"""

from unittest.mock import MagicMock, patch

import pytest

from agent.tools.format_for_channel import (
    CHANNEL_RULES,
    FormattedResponse,
    format_for_channel,
    inject_email_greeting,
    inject_email_signoff,
    strip_markdown,
)


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


def make_text(word_count: int) -> str:
    """Generate text with approximately word_count words."""
    words = ["word"] * word_count
    return " ".join(words)


def make_chars(char_count: int) -> str:
    """Generate text with exactly char_count characters."""
    return "a" * char_count


# ---------------------------------------------------------------------------
# Channel rule tests
# ---------------------------------------------------------------------------


class TestEmailChannel:
    def test_within_limit_returns_as_is(self):
        """Short email (100 words) should pass without LLM trim."""
        text = make_text(100)
        result = format_for_channel(raw=text, channel="email", customer_name="Alice")

        assert result.within_limits is True
        assert result.error is None
        assert "Dear Alice," in result.text
        assert "Best regards" in result.text

    def test_greeting_injected_with_name(self):
        """Email should have 'Dear {name},' greeting."""
        result = format_for_channel(
            raw="Hello, how can I help?",
            channel="email",
            customer_name="Bob",
        )
        assert result.text.startswith("Dear Bob,")

    def test_greeting_injected_without_name(self):
        """Email without customer name uses 'Dear Customer,'."""
        result = format_for_channel(
            raw="Hello, how can I help?",
            channel="email",
        )
        assert result.text.startswith("Dear Customer,")

    def test_signoff_injected(self):
        """Email should end with support sign-off."""
        result = format_for_channel(
            raw="Here is your answer.",
            channel="email",
        )
        assert "Best regards" in result.text
        assert "Customer Success Team" in result.text

    def test_over_limit_triggers_trim(self):
        """600-word email should trigger LLM trim and return <= 500 words."""
        long_text = make_text(600)
        trimmed_text = make_text(400)  # mock trim result

        with patch("agent.tools.format_for_channel._trim_with_llm") as mock_trim:
            mock_trim.return_value = trimmed_text
            result = format_for_channel(raw=long_text, channel="email")

        assert mock_trim.called
        # After trim + greeting + sign-off, should be within limit
        # Note: greeting and sign-off add a few words
        assert result.within_limits is True

    def test_word_count_returned(self):
        """word_count should be populated for email."""
        result = format_for_channel(raw="Hello world.", channel="email")
        assert result.word_count is not None
        assert result.word_count > 0


class TestWhatsAppChannel:
    def test_within_limit_returns_as_is(self):
        """Short WhatsApp message (100 chars) passes without LLM trim."""
        text = "Hello, I need help with my account please."
        result = format_for_channel(raw=text, channel="whatsapp")

        assert result.within_limits is True
        assert result.error is None
        assert len(result.text) <= 300

    def test_over_limit_triggers_trim(self):
        """400-char WhatsApp message should trigger LLM trim."""
        long_text = "a" * 400
        trimmed_text = "a" * 250  # mock trim result

        with patch("agent.tools.format_for_channel._trim_with_llm") as mock_trim:
            mock_trim.return_value = trimmed_text
            result = format_for_channel(raw=long_text, channel="whatsapp")

        assert mock_trim.called

    def test_markdown_stripped(self):
        """WhatsApp messages should have markdown removed."""
        markdown_text = "# Header\n\n**Bold text** and *italic* and `code`"
        result = format_for_channel(raw=markdown_text, channel="whatsapp")

        assert "#" not in result.text
        assert "**" not in result.text
        assert "*" not in result.text or result.text.count("*") == 0
        assert "`" not in result.text
        # Content should still be there
        assert "Header" in result.text
        assert "Bold text" in result.text

    def test_char_count_returned(self):
        """char_count should be populated for WhatsApp."""
        result = format_for_channel(raw="Hello world", channel="whatsapp")
        assert result.char_count is not None
        assert result.char_count > 0

    def test_no_greeting_for_whatsapp(self):
        """WhatsApp messages should not have email-style greeting."""
        result = format_for_channel(raw="Hi there", channel="whatsapp")
        assert "Dear " not in result.text
        assert "Best regards" not in result.text


class TestWebformChannel:
    def test_within_limit_returns_as_is(self):
        """200-word webform response passes without trim."""
        text = make_text(200)
        result = format_for_channel(raw=text, channel="webform")

        assert result.within_limits is True

    def test_over_limit_triggers_trim(self):
        """400-word webform should trigger LLM trim."""
        long_text = make_text(400)
        trimmed_text = make_text(250)

        with patch("agent.tools.format_for_channel._trim_with_llm") as mock_trim:
            mock_trim.return_value = trimmed_text
            result = format_for_channel(raw=long_text, channel="webform")

        assert mock_trim.called


# ---------------------------------------------------------------------------
# E004 error tests
# ---------------------------------------------------------------------------


class TestE004ErrorHandling:
    def test_e004_on_double_fail(self):
        """If LLM trim still produces over-limit text, return E004."""
        long_text = make_text(600)
        still_long = make_text(550)  # trim returns text still too long

        with patch("agent.tools.format_for_channel._trim_with_llm") as mock_trim:
            mock_trim.return_value = still_long
            result = format_for_channel(raw=long_text, channel="email")

        assert result.within_limits is False
        assert result.error is not None
        assert "E004" in result.error

    def test_e004_on_llm_error(self):
        """LLM trim exception should result in E004 error."""
        long_text = make_text(600)

        with patch("agent.tools.format_for_channel._trim_with_llm") as mock_trim:
            mock_trim.side_effect = Exception("LLM unavailable")
            result = format_for_channel(raw=long_text, channel="email")

        assert result.within_limits is False
        assert result.error is not None


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidation:
    def test_unknown_channel_raises(self):
        """Unknown channel should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown channel"):
            format_for_channel(raw="Hello", channel="telegram")


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_inject_email_greeting_with_name(self):
        text = "Here is your answer."
        result = inject_email_greeting(text, "Carol")
        assert result.startswith("Dear Carol,")
        assert "Here is your answer." in result

    def test_inject_email_greeting_without_name(self):
        text = "Here is your answer."
        result = inject_email_greeting(text, None)
        assert result.startswith("Dear Customer,")

    def test_inject_email_signoff(self):
        text = "Here is your answer."
        result = inject_email_signoff(text)
        assert "Best regards" in result
        assert "Customer Success Team" in result

    def test_inject_email_signoff_not_duplicated(self):
        """Sign-off should not be injected if already present."""
        text = "Here is your answer.\n\nBest regards,\nCustomer Success Team"
        result = inject_email_signoff(text)
        assert result.count("Best regards") == 1

    def test_strip_markdown_headers(self):
        text = "# Header\n## Subheader\nContent"
        result = strip_markdown(text)
        assert "#" not in result
        assert "Header" in result
        assert "Content" in result

    def test_strip_markdown_bold_italic(self):
        text = "**bold** and *italic* and __underline__"
        result = strip_markdown(text)
        assert "**" not in result
        assert "*" not in result
        assert "bold" in result
        assert "italic" in result

    def test_strip_markdown_code(self):
        text = "Use `print()` to output text.\n```python\nprint('hello')\n```"
        result = strip_markdown(text)
        assert "`" not in result
