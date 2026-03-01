"""
database/seed_kb.py — Seed the knowledge_base table with 15 FAQ articles.

Covers: account management, billing, integrations, troubleshooting.
Generates embeddings using OpenAI text-embedding-3-small.
Run after migrations: python database/seed_kb.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_db_context
from database.repositories.kb_repo import upsert_kb_article

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FAQ_ARTICLES = [
    # --- Account Management ---
    {
        "title": "How to Reset Your Password",
        "content": """To reset your password, follow these steps:

1. Go to the login page and click "Forgot Password" below the password field.
2. Enter your registered email address and click "Send Reset Link".
3. Check your email inbox (and spam folder) for a password reset email.
4. Click the reset link in the email — it expires in 1 hour.
5. Enter your new password (minimum 8 characters, must include one number).
6. Click "Save New Password" and log in with your new credentials.

If you don't receive the email within 5 minutes, check your spam folder or contact support. Make sure you're using the email address associated with your account.

Common issues:
- Reset link expired: request a new one from the login page
- Email not arriving: check spam, or try an alternate email if you have multiple accounts
- Account locked: after 5 failed attempts, accounts are locked for 30 minutes""",
        "topic_tags": ["account", "password", "authentication", "security"],
        "source_url": "/help/password-reset",
    },
    {
        "title": "Setting Up Two-Factor Authentication (2FA)",
        "content": """Two-factor authentication (2FA) adds an extra layer of security to your account.

To enable 2FA:
1. Log into your account and navigate to Settings > Security.
2. Click "Enable Two-Factor Authentication".
3. Choose your preferred method: Authenticator App (recommended) or SMS.
4. For Authenticator App: scan the QR code with Google Authenticator, Authy, or similar app.
5. Enter the 6-digit code from your authenticator to confirm setup.
6. Save your backup codes in a secure location — these are used if you lose your device.

For SMS authentication:
1. Enter your mobile phone number in E.164 format (e.g., +1 415 555 1234).
2. Enter the verification code sent to your phone.

To disable 2FA: go to Settings > Security > Disable 2FA and enter your current 2FA code.

Backup codes: you receive 10 one-time backup codes at setup. Each can only be used once. Generate new codes from Settings > Security > Regenerate Backup Codes.""",
        "topic_tags": ["account", "security", "2fa", "authentication"],
        "source_url": "/help/two-factor-authentication",
    },
    {
        "title": "Updating Your Profile and Account Information",
        "content": """You can update your profile information at any time from the account settings page.

To update basic information:
1. Click your avatar in the top-right corner and select "Profile Settings".
2. Edit your display name, company name, and profile picture.
3. Click "Save Changes".

To update your email address:
1. Go to Settings > Account > Email.
2. Enter your new email address and current password to confirm.
3. A verification email will be sent to the new address.
4. Click the verification link to confirm the change.
Note: Your old email will receive a notification of the change.

To update your password:
1. Go to Settings > Security > Change Password.
2. Enter your current password and new password.
3. Click "Update Password".

Timezone and language settings can be updated in Settings > Preferences.""",
        "topic_tags": ["account", "profile", "settings"],
        "source_url": "/help/profile-settings",
    },

    # --- Billing ---
    {
        "title": "Understanding Your Billing and Subscription Plans",
        "content": """We offer three subscription plans designed for different team sizes and needs.

Starter Plan ($29/month):
- Up to 3 users
- 1,000 customer conversations per month
- Email support channel
- 30-day message history

Professional Plan ($99/month):
- Up to 15 users
- 10,000 conversations per month
- Email + WhatsApp channels
- 90-day message history
- Priority support

Enterprise Plan (custom pricing):
- Unlimited users
- Unlimited conversations
- All channels including custom integrations
- Unlimited history
- Dedicated account manager
- SLA guarantee

All plans are billed monthly or annually (annual = 2 months free). Payment methods accepted: Visa, Mastercard, American Express, PayPal.

For billing questions, refunds, or plan changes, please contact our billing team directly as these require human review.""",
        "topic_tags": ["billing", "pricing", "subscription", "plans"],
        "source_url": "/help/billing-plans",
    },
    {
        "title": "How to Upgrade or Downgrade Your Plan",
        "content": """You can change your subscription plan at any time from the Billing settings page.

To upgrade your plan:
1. Go to Settings > Billing > Change Plan.
2. Select the plan you want to upgrade to.
3. Review the pricing and prorated charge for the remainder of your billing cycle.
4. Confirm the upgrade — your new features activate immediately.

To downgrade your plan:
1. Go to Settings > Billing > Change Plan.
2. Select the lower-tier plan.
3. Review what features you will lose.
4. Confirm — the downgrade takes effect at the end of your current billing period.

Important notes:
- Upgrades are prorated (you pay only for the remainder of the month).
- Downgrades take effect at the next renewal date.
- If your current usage exceeds the limits of the downgrade plan, you will be asked to reduce usage first.

For cancellation or refund requests, please contact our billing team directly.""",
        "topic_tags": ["billing", "upgrade", "downgrade", "subscription"],
        "source_url": "/help/change-plan",
    },

    # --- Integrations ---
    {
        "title": "Setting Up Single Sign-On (SSO)",
        "content": """Single Sign-On (SSO) is available on the Enterprise plan and allows your team to log in using your company's identity provider.

Supported SSO providers:
- SAML 2.0 (Google Workspace, Okta, Azure AD, OneLogin)
- OAuth 2.0 / OpenID Connect

To configure SSO:
1. Go to Settings > Security > Single Sign-On.
2. Download the Service Provider (SP) metadata XML.
3. Upload this metadata to your identity provider (IdP).
4. Enter your IdP metadata URL or XML in our SSO configuration.
5. Set the attribute mapping (email, name, role).
6. Test the connection using the "Test SSO" button.
7. Enable SSO enforcement (optional — users can still use password login if disabled).

Troubleshooting SSO:
- "User not provisioned": ensure the email attribute is correctly mapped in your IdP.
- "Invalid assertion": check that clock skew between your IdP and our servers is under 5 minutes.
- Contact support with your SAML assertion XML for debugging.""",
        "topic_tags": ["integrations", "sso", "security", "authentication"],
        "source_url": "/help/sso-setup",
    },
    {
        "title": "Creating and Managing API Keys",
        "content": """API keys allow you to integrate our platform with your own applications and scripts.

To create an API key:
1. Go to Settings > Developers > API Keys.
2. Click "Create New API Key".
3. Enter a descriptive name (e.g., "Production Integration", "CI/CD Pipeline").
4. Select the permission scope: Read-Only, Read-Write, or Admin.
5. Click "Generate Key" — copy and store it securely. You will not be able to view it again.

API key best practices:
- Use separate keys for each application or environment.
- Never commit API keys to version control — use environment variables.
- Rotate keys every 90 days.
- Set IP allowlists on keys where possible (Settings > API Key > Restrict to IP).

To revoke an API key:
1. Go to Settings > Developers > API Keys.
2. Find the key and click "Revoke".
3. The key is invalidated immediately.

Rate limits: 1,000 requests per minute per API key. See our API documentation for full endpoint reference.""",
        "topic_tags": ["integrations", "api", "developers", "security"],
        "source_url": "/help/api-keys",
    },
    {
        "title": "Configuring Webhooks",
        "content": """Webhooks allow our platform to send real-time event notifications to your server.

Supported events:
- ticket.created, ticket.updated, ticket.resolved, ticket.escalated
- message.received, message.sent
- customer.created, customer.updated

To set up a webhook:
1. Go to Settings > Developers > Webhooks.
2. Click "Add Webhook Endpoint".
3. Enter your endpoint URL (must be HTTPS).
4. Select the events you want to receive.
5. Optionally set a secret key for HMAC-SHA256 signature verification.
6. Click "Save" — a test event will be sent immediately.

Verifying webhook signatures:
The X-Webhook-Signature header contains: HMAC-SHA256(secret, request_body).
Compare this with your own HMAC calculation to verify authenticity.

Retry policy: Failed deliveries (non-2xx responses) are retried 3 times with exponential backoff (5s, 30s, 5min).

Troubleshooting: Check the webhook delivery logs in Settings > Developers > Webhooks > Delivery History.""",
        "topic_tags": ["integrations", "webhooks", "developers", "api"],
        "source_url": "/help/webhooks",
    },

    # --- Troubleshooting ---
    {
        "title": "Troubleshooting Login Issues",
        "content": """If you're having trouble logging in, here are the most common causes and solutions.

Issue: "Invalid email or password"
- Double-check your email address spelling (must match exactly what you registered with).
- Passwords are case-sensitive. Make sure Caps Lock is off.
- Try resetting your password via "Forgot Password" on the login page.

Issue: "Account locked"
- Accounts are temporarily locked after 5 failed login attempts.
- Wait 30 minutes and try again, or use "Forgot Password" to reset.

Issue: 2FA code not working
- Ensure your device clock is accurate (2FA codes are time-sensitive).
- Try the next code generated by your authenticator app.
- If still failing, use one of your backup codes.

Issue: SSO login failing
- Confirm your company SSO is configured correctly in Settings > Security.
- Try logging in with email/password instead as a fallback.
- Contact your IT administrator to verify your IdP configuration.

Issue: Browser not loading the app
- Clear browser cache and cookies (Ctrl+Shift+Del).
- Try an incognito/private browser window.
- Ensure JavaScript is enabled.
- Try a different browser (Chrome, Firefox, Safari, Edge all supported).""",
        "topic_tags": ["troubleshooting", "login", "account", "authentication"],
        "source_url": "/help/login-troubleshooting",
    },
    {
        "title": "Troubleshooting Slow Performance",
        "content": """If the application is loading slowly or not responding as expected, try these steps.

Quick fixes to try first:
1. Refresh the page (Ctrl+R or Cmd+R).
2. Clear your browser cache (Ctrl+Shift+Del).
3. Disable browser extensions — some ad-blockers or privacy tools can interfere.
4. Try a different browser.
5. Check your internet connection speed at fast.com.

Checking platform status:
- Visit status.ourplatform.com for real-time service status.
- Subscribe to status updates to be notified of incidents.

If the issue persists:
- Check if you're processing large data sets — exports or bulk operations may temporarily slow the UI.
- For team-wide slowness, contact support with your account ID and the time the issue started.
- Include browser console errors (F12 > Console tab) if available.

Known performance scenarios:
- Bulk exports > 10,000 rows: these run in the background and you'll receive an email when ready.
- Dashboard loading: complex date ranges with many filters may take 5–10 seconds for large accounts.""",
        "topic_tags": ["troubleshooting", "performance", "browser"],
        "source_url": "/help/performance",
    },
    {
        "title": "Exporting Your Data",
        "content": """You can export your data at any time from the platform in CSV or JSON format.

To export customer data:
1. Go to Customers > Export.
2. Choose date range and field filters.
3. Select format: CSV or JSON.
4. Click "Start Export".
5. Large exports (>10,000 records) run in the background — you'll receive an email with a download link.

To export ticket history:
1. Go to Tickets > Export.
2. Filter by channel, status, date range.
3. Click "Export CSV".

To export all your account data (GDPR data portability):
1. Go to Settings > Privacy > Export My Data.
2. Click "Request Full Data Export".
3. You will receive a download link within 24 hours containing all data associated with your account.

Data retention:
- Starter plan: 30 days
- Professional plan: 90 days
- Enterprise: unlimited (configurable)

Note: Exports older than your plan's retention period are not available. Contact sales to discuss enterprise archiving options.""",
        "topic_tags": ["data", "export", "gdpr", "privacy"],
        "source_url": "/help/data-export",
    },
    {
        "title": "Managing Team Members and Permissions",
        "content": """You can invite team members and control their access levels from the Team settings.

To invite a team member:
1. Go to Settings > Team > Invite Members.
2. Enter the email address of the person to invite.
3. Select their role: Admin, Agent, or Viewer.
4. Click "Send Invitation".
5. They'll receive an invitation email valid for 7 days.

Roles and permissions:
- Admin: full access including billing and settings changes
- Agent: can view and respond to tickets, cannot change settings or billing
- Viewer: read-only access to tickets and reports

To remove a team member:
1. Go to Settings > Team.
2. Find the member and click "Remove".
3. Their access is revoked immediately.
4. Tickets assigned to them remain but are unassigned.

To transfer ownership (change the account owner):
1. Go to Settings > Team > Transfer Ownership.
2. Select the new owner from your team members.
3. Confirm the transfer — you will be downgraded to Admin role.""",
        "topic_tags": ["team", "permissions", "settings", "account"],
        "source_url": "/help/team-management",
    },
    {
        "title": "Setting Up Email Channel Integration",
        "content": """Connect your support email address to receive and respond to customer emails through the platform.

To connect a Gmail account:
1. Go to Settings > Channels > Email.
2. Click "Connect Gmail Account".
3. Authorize access using your Google account credentials.
4. Select the Gmail label/folder to monitor for support emails.
5. Configure the reply-from address.

To connect a custom email (IMAP/SMTP):
1. Go to Settings > Channels > Email > Custom Email.
2. Enter your IMAP server settings (server, port, SSL/TLS, username, password).
3. Enter your SMTP settings for sending replies.
4. Click "Test Connection" to verify.
5. Set the email address customers should write to.

To set up email forwarding:
- Forward emails from support@yourcompany.com to your unique platform forwarding address.
- The forwarding address is shown in Settings > Channels > Email > Forwarding Address.

Auto-routing rules:
- Set up keyword-based routing to assign tickets to specific agents or queues.
- Configure auto-response templates for after-hours messages.""",
        "topic_tags": ["channels", "email", "integration", "setup"],
        "source_url": "/help/email-channel",
    },
    {
        "title": "Setting Up WhatsApp Business Channel",
        "content": """Connect your WhatsApp Business number to receive and respond to customer WhatsApp messages.

Requirements:
- A WhatsApp Business API account (via Meta or a BSP like Twilio)
- A verified phone number for WhatsApp Business

To connect via Twilio:
1. Go to Settings > Channels > WhatsApp.
2. Click "Connect via Twilio".
3. Enter your Twilio Account SID and Auth Token.
4. Enter your Twilio WhatsApp-enabled number (format: +14155238886).
5. Set the webhook URL in your Twilio console to: https://yourplatform.com/webhooks/whatsapp.
6. Click "Test Connection" to verify.

Message templates:
- Outbound messages outside the 24-hour customer service window require pre-approved templates.
- Go to Settings > Channels > WhatsApp > Templates to create and submit templates.

Limitations:
- Messages are limited to 300 characters for our automated responses.
- Media (images, documents) in inbound messages are stored but not processed by AI.""",
        "topic_tags": ["channels", "whatsapp", "integration", "setup"],
        "source_url": "/help/whatsapp-channel",
    },
    {
        "title": "Understanding Your Ticket Dashboard and Reports",
        "content": """The ticket dashboard gives you a real-time overview of your support operations.

Dashboard sections:
- Overview: total open tickets, response time average, resolution rate, CSAT score
- Queue: tickets sorted by priority and channel, with agent assignment controls
- Trends: charts showing volume by channel, day of week, and time of day

Daily reports:
- Available in Reports > Daily for each day's summary.
- Shows: total tickets, tickets by channel, escalation rate, mean sentiment, top topics.
- Reports are generated daily at 7am UTC.

Key metrics explained:
- First Response Time: time from ticket creation to first AI or human response
- Resolution Time: time from ticket creation to resolved status
- Escalation Rate: percentage of tickets escalated to human agents (target: <20%)
- Mean Sentiment: average customer sentiment score (0=very negative, 1=very positive)
- CSAT: Customer Satisfaction Score from post-resolution surveys

Exporting reports:
- Go to Reports > Export to download CSV of any date range.
- Scheduled email reports can be configured in Reports > Schedule.""",
        "topic_tags": ["reports", "dashboard", "analytics", "metrics"],
        "source_url": "/help/reports",
    },
]


async def seed_knowledge_base():
    """Seed all 15 FAQ articles into the knowledge_base table."""
    logger.info("Starting knowledge base seeding (%d articles)...", len(FAQ_ARTICLES))

    async with get_db_context() as session:
        for i, article in enumerate(FAQ_ARTICLES, 1):
            logger.info(
                "Processing article %d/%d: %s",
                i,
                len(FAQ_ARTICLES),
                article["title"],
            )
            await upsert_kb_article(
                session=session,
                title=article["title"],
                content=article["content"],
                topic_tags=article["topic_tags"],
                source_url=article.get("source_url"),
            )

    logger.info("Knowledge base seeding complete. %d articles inserted.", len(FAQ_ARTICLES))


if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())
