"""
channels/gmail/sender.py — Send Gmail replies in the same thread.

send_gmail_reply(thread_id, to_address, subject, html_body) -> bool
  - Asserts word count <= 500 before sending
  - Returns False (does not raise) on Gmail API errors
"""

import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

EMAIL_MAX_WORDS = 500


def _count_words(text: str) -> int:
    """Count words in HTML/text by stripping tags."""
    import re
    # Remove HTML tags for word count
    plain = re.sub(r"<[^>]+>", " ", text)
    return len(plain.split())


def _get_gmail_service():
    """Build authenticated Gmail API service for sending."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            settings.gmail_credentials_path,
            scopes=[
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.readonly",
            ],
        )
        service = build("gmail", "v1", credentials=credentials)
        return service
    except Exception as e:
        logger.error("Failed to build Gmail service for sending: %s", e)
        raise


async def send_gmail_reply(
    thread_id: str,
    to_address: str,
    subject: str,
    html_body: str,
) -> bool:
    """
    Send a reply in an existing Gmail thread.

    Args:
        thread_id: Gmail thread ID to reply in
        to_address: recipient email address
        subject: email subject line
        html_body: HTML-formatted body (max 500 words when stripped of tags)

    Returns:
        True on success, False on any error (does not raise)
    """
    # Check word count guard
    word_count = _count_words(html_body)
    assert word_count <= EMAIL_MAX_WORDS, (
        f"Email body exceeds {EMAIL_MAX_WORDS} words ({word_count})"
    )

    if not settings.gmail_credentials_path or not settings.gmail_support_address:
        logger.warning(
            "Gmail credentials not configured — email reply not sent to %s",
            to_address[:5] + "***@***",
        )
        return False

    try:
        service = _get_gmail_service()

        # Build the MIME message
        msg = MIMEMultipart("alternative")
        msg["To"] = to_address
        msg["From"] = settings.gmail_support_address
        msg["Subject"] = subject

        # Attach plain text and HTML versions
        plain_text = html_body.replace("<br>", "\n").replace("<br/>", "\n")
        import re
        plain_text = re.sub(r"<[^>]+>", "", plain_text)

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # Encode for Gmail API
        raw_message = base64.urlsafe_b64encode(
            msg.as_bytes()
        ).decode("utf-8")

        # Send in thread
        send_body = {
            "raw": raw_message,
            "threadId": thread_id,
        }

        sent = service.users().messages().send(
            userId="me",
            body=send_body,
        ).execute()

        logger.info(
            "Gmail reply sent: message_id=%s, thread=%s, to=%s***",
            sent.get("id"),
            thread_id,
            to_address[:5],
        )
        return True

    except AssertionError:
        raise  # Re-raise assertion errors (word count check)
    except Exception as e:
        logger.error("Gmail send_gmail_reply failed: %s", e)
        return False
