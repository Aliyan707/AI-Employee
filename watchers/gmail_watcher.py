"""Gmail Watcher for Silver-tier AI Employee system.

Monitors Gmail inbox for important/unread messages and creates
EMAIL_*.md files in Needs_Action/Email/ for processing.
"""

import os
from pathlib import Path
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import base64
from email import message_from_bytes
from base_watcher import BaseWatcher


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    """Watches Gmail inbox for important/unread emails.

    Creates EMAIL_*.md files in Needs_Action/Email/ with:
    - Sender, subject, received time
    - Email snippet/preview
    - Priority classification
    - Suggested actions
    """

    def __init__(self, vault_path: str, credentials_path: str, token_path: str = None):
        """Initialize Gmail watcher.

        Args:
            vault_path: Path to Obsidian vault
            credentials_path: Path to Gmail API credentials.json
            token_path: Path to store OAuth token (default: vault/System/gmail_token.pickle)
        """
        super().__init__(vault_path, check_interval=120)  # Check every 2 minutes

        self.credentials_path = credentials_path
        self.token_path = token_path or str(self.vault_path / 'System' / 'gmail_token.pickle')
        self.service = None
        self.processed_ids = set()

        # Ensure Email subfolder exists
        self.email_folder = self.needs_action / 'Email'
        self.email_folder.mkdir(parents=True, exist_ok=True)

        # Authenticate
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info('Refreshing expired credentials')
                creds.refresh(Request())
            else:
                self.logger.info('No valid credentials, starting OAuth flow')
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
            self.logger.info(f'Credentials saved to {self.token_path}')

        # Build Gmail service
        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info('Gmail API authenticated successfully')

    def check_for_updates(self):
        """Check Gmail for unread important messages.

        Returns:
            List of message objects (dict with id, threadId)
        """
        try:
            # Query for unread important messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread is:important',
                maxResults=10
            ).execute()

            messages = results.get('messages', [])

            # Filter out already processed messages
            new_messages = [
                m for m in messages
                if m['id'] not in self.processed_ids
            ]

            return new_messages

        except HttpError as error:
            self.logger.error(f'Gmail API error: {error}')
            return []

    def create_action_file(self, message: dict) -> Path:
        """Create EMAIL_*.md file from Gmail message.

        Args:
            message: Gmail message object with 'id' field

        Returns:
            Path to created markdown file
        """
        try:
            # Get full message details
            msg = self.service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()

            # Extract headers
            headers = {
                h['name']: h['value']
                for h in msg['payload']['headers']
            }

            from_addr = headers.get('From', 'Unknown')
            subject = headers.get('Subject', 'No Subject')
            date_received = headers.get('Date', '')

            # Get email body snippet
            snippet = msg.get('snippet', '')

            # Classify priority based on subject/sender
            priority = self._classify_priority(subject, from_addr, snippet)

            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            msg_id_short = message['id'][:8]
            filename = f'EMAIL_{timestamp}_{msg_id_short}.md'
            filepath = self.email_folder / filename

            # Create markdown content
            content = f'''---
type: email
from: {from_addr}
subject: {subject}
received: {self.format_timestamp()}
original_date: {date_received}
priority: {priority}
status: pending
gmail_id: {message['id']}
---

## Email Preview
{snippet}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
- [ ] Flag for human review

## Notes
Created by Gmail Watcher at {self.format_timestamp()}
'''

            # Write file
            filepath.write_text(content, encoding='utf-8')

            # Mark as processed
            self.processed_ids.add(message['id'])

            return filepath

        except Exception as e:
            self.logger.error(f'Error creating action file for message {message["id"]}: {e}')
            raise

    def _classify_priority(self, subject: str, from_addr: str, snippet: str) -> str:
        """Classify email priority based on content.

        Args:
            subject: Email subject line
            from_addr: Sender address
            snippet: Email preview text

        Returns:
            Priority level: 'high', 'medium', or 'low'
        """
        subject_lower = subject.lower()
        snippet_lower = snippet.lower()

        # High priority keywords
        high_keywords = [
            'urgent', 'asap', 'important', 'deadline',
            'payment', 'invoice', 'overdue', 'critical'
        ]

        if any(kw in subject_lower or kw in snippet_lower for kw in high_keywords):
            return 'high'

        # Medium priority by default (since we're only watching important emails)
        return 'medium'


if __name__ == '__main__':
    """Run Gmail watcher standalone for testing."""
    import sys

    if len(sys.argv) < 3:
        print('Usage: python gmail_watcher.py <vault_path> <credentials_path>')
        sys.exit(1)

    vault_path = sys.argv[1]
    credentials_path = sys.argv[2]

    watcher = GmailWatcher(vault_path, credentials_path)
    watcher.run()
