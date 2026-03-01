"""
agent/tools/format_for_channel.py — Pure function for channel-specific response formatting.

PURE FUNCTION: No I/O side effects except the LLM trim call when content exceeds limits.

Channel rules:
  - email: ≤500 words, formal, greeting + sign-off required
  - whatsapp: ≤300 chars, conversational, plain text
  - webform: ≤300 words, semi-formal
"""

import re
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Channel rules configuration
# ---------------------------------------------------------------------------

CHANNEL_RULES: dict = {
    "email": {
        "max_words": 500,
        "tone": "formal and professional",
        "unit": "words",
        "markdown": True,
        "requires_greeting": True,
        "requires_signoff": True,
    },
    "whatsapp": {
        "max_chars": 300,
        "tone": "conversational and warm",
        "unit": "characters",
        "markdown": False,
        "strip_markdown": True,
        "requires_greeting": False,
        "requires_signoff": False,
    },
    "webform": {
        "max_words": 300,
        "tone": "semi-formal and helpful",
        "unit": "words",
        "markdown": True,
        "requires_greeting": False,
        "requires_signoff": False,
    },
}


@dataclass
class FormattedResponse:
    """Result of format_for_channel."""
    text: str
    within_limits: bool
    word_count: Optional[int]   # for email/webform
    char_count: Optional[int]   # for whatsapp
    error: Optional[str]        # "E004" detail if within_limits=False after retry


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def count_words(text: str) -> int:
    """Count words in text by splitting on whitespace."""
    return len(text.split())


def count_chars(text: str) -> int:
    """Count characters in text."""
    return len(text)


def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting for WhatsApp plain text.
    - Remove headers (# ## ###)
    - Remove bold/italic (**text** *text*)
    - Remove code blocks (```...```)
    - Remove inline code (`code`)
    - Remove bullet characters and convert to plain
    - Remove horizontal rules
    """
    # Remove fenced code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Remove inline code
    text = re.sub(r"`[^`]+`", "", text)
    # Remove headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
    # Remove horizontal rules
    text = re.sub(r"^[-*_]{3,}$", "", text, flags=re.MULTILINE)
    # Clean up extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def inject_email_greeting(
    text: str,
    customer_name: Optional[str],
) -> str:
    """Inject 'Dear {name},' greeting at the beginning for email channel."""
    if customer_name:
        greeting = f"Dear {customer_name},"
    else:
        greeting = "Dear Customer,"
    return f"{greeting}\n\n{text}"


def inject_email_signoff(text: str) -> str:
    """Inject professional sign-off at the end for email channel."""
    signoff = "\n\nBest regards,\nCustomer Success Team"
    # Avoid double sign-off
    if "Best regards" not in text and "Customer Success Team" not in text:
        return text + signoff
    return text


def _trim_with_llm(
    raw: str,
    channel: str,
    limit: int,
    unit: str,
) -> str:
    """
    Call GPT-4o to trim the response to fit within channel limits.
    Uses synchronous OpenAI client (called inline in pure function).
    """
    rules = CHANNEL_RULES[channel]
    tone = rules["tone"]

    prompt = f"""You are a response editor. Rewrite the following customer support response for the {channel} channel.

Requirements:
- Tone: {tone}
- Maximum: {limit} {unit}
- Preserve all factual content; cut filler words and redundant sentences first
- Do NOT add new information
- Do NOT include greetings or sign-offs (those are added separately)
- Output ONLY the trimmed response text, nothing else

Response to trim:
{raw}"""

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------


def format_for_channel(
    raw: str,
    channel: str,
    customer_name: Optional[str] = None,
    retry: bool = False,
) -> FormattedResponse:
    """
    Format a raw response string for the specified channel.

    Pure function — only side effect is the LLM call when trimming.

    Algorithm:
    1. Strip markdown for WhatsApp
    2. Check length against channel limits
    3. If within limits: inject greeting/sign-off (email only), return
    4. If over limit: call LLM trim with exact budget
    5. Re-check after trim
    6. If still over: return FormattedResponse(within_limits=False, error="E004")

    Args:
        raw: The raw response text to format
        channel: "email" | "whatsapp" | "webform"
        customer_name: Customer's display name (used in email greeting)
        retry: True if this is a second attempt (disables further LLM calls)

    Returns:
        FormattedResponse with formatted text and metadata
    """
    if channel not in CHANNEL_RULES:
        raise ValueError(f"Unknown channel: {channel}. Must be one of {list(CHANNEL_RULES)}")

    rules = CHANNEL_RULES[channel]
    text = raw.strip()

    # Step 1: Strip markdown for WhatsApp
    if rules.get("strip_markdown"):
        text = strip_markdown(text)

    # Step 2: Check limits
    if channel == "whatsapp":
        current_count = count_chars(text)
        limit = rules["max_chars"]
        unit = "characters"
        within = current_count <= limit
    else:
        current_count = count_words(text)
        limit = rules["max_words"]
        unit = "words"
        within = current_count <= limit

    # Step 3: If within limits, apply formatting and return
    if within:
        if rules.get("requires_greeting"):
            text = inject_email_greeting(text, customer_name)
        if rules.get("requires_signoff"):
            text = inject_email_signoff(text)

        final_chars = count_chars(text)
        final_words = count_words(text) if channel != "whatsapp" else None

        return FormattedResponse(
            text=text,
            within_limits=True,
            word_count=final_words,
            char_count=final_chars,
            error=None,
        )

    # Step 4: Over limit — if already retried, return E004
    if retry:
        return FormattedResponse(
            text=text,
            within_limits=False,
            word_count=count_words(text) if channel != "whatsapp" else None,
            char_count=count_chars(text),
            error="E004: Response exceeds channel limits after reformat attempt",
        )

    # Step 5: LLM trim
    try:
        trimmed = _trim_with_llm(text, channel, limit, unit)
    except Exception:
        # If LLM trim fails, return as-is with error
        return FormattedResponse(
            text=text,
            within_limits=False,
            word_count=count_words(text) if channel != "whatsapp" else None,
            char_count=count_chars(text),
            error="E004: Trim failed — LLM error",
        )

    # Step 6: Re-check after trim (recursive call with retry=True)
    return format_for_channel(trimmed, channel, customer_name, retry=True)
