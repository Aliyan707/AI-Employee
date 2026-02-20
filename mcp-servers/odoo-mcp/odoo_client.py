"""Odoo JSON-RPC client wrapper for MCP server.

Provides simplified interface to Odoo Community 19+ External API.
Uses odoorpc library for XML-RPC/JSON-RPC communication.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import odoorpc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class OdooClient:
    """Wrapper for Odoo RPC operations.

    Handles connection, authentication, and common operations for
    Gold-tier AI Employee accounting automation.
    """

    def __init__(self):
        """Initialize Odoo client from environment variables."""
        self.url = os.getenv('ODOO_URL', 'http://localhost:8069')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME')

        # Read password from file (never store in env directly)
        password_file = os.getenv('ODOO_PASSWORD_FILE')
        if password_file and Path(password_file).exists():
            with open(password_file, 'r') as f:
                self.password = f.read().strip()
        else:
            self.password = None
            logger.warning("ODOO_PASSWORD_FILE not found - client will fail to connect")

        self.odoo: Optional[odoorpc.ODOO] = None
        self._connect()

    def _connect(self):
        """Establish connection to Odoo instance."""
        if not all([self.url, self.db, self.username, self.password]):
            logger.error("Missing Odoo credentials in environment")
            raise ValueError("Odoo credentials incomplete - check .env file")

        try:
            # Parse URL to get host and port
            from urllib.parse import urlparse
            parsed = urlparse(self.url)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 8069
            protocol = 'jsonrpc+ssl' if parsed.scheme == 'https' else 'jsonrpc'

            logger.info(f"Connecting to Odoo at {host}:{port} (protocol: {protocol})")

            self.odoo = odoorpc.ODOO(host, port=port, protocol=protocol)
            self.odoo.login(self.db, self.username, self.password)

            logger.info(f"Connected to Odoo as {self.username}")

        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
            raise

    def create_draft_invoice(
        self,
        partner_id: int,
        amount: float,
        currency: str = 'PKR',
        description: str = '',
        invoice_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create draft invoice in Odoo.

        Args:
            partner_id: Odoo partner (customer) ID
            amount: Invoice amount
            currency: Currency code (default: PKR)
            description: Invoice description/reference
            invoice_date: Invoice date (YYYY-MM-DD) or None for today

        Returns:
            Dict with draft_id, state, preview info
        """
        if not self.odoo:
            raise RuntimeError("Not connected to Odoo")

        try:
            AccountMove = self.odoo.env['account.move']

            # Create invoice draft
            invoice_vals = {
                'partner_id': partner_id,
                'move_type': 'out_invoice',  # Customer invoice
                'invoice_date': invoice_date,
                'ref': description,
                'currency_id': self._get_currency_id(currency),
                'state': 'draft',  # Keep as draft until confirmed
            }

            draft_id = AccountMove.create(invoice_vals)

            logger.info(f"Created draft invoice {draft_id} for partner {partner_id}")

            return {
                'draft_id': draft_id,
                'state': 'draft',
                'partner_id': partner_id,
                'amount': amount,
                'currency': currency,
                'description': description,
            }

        except Exception as e:
            logger.error(f"Failed to create draft invoice: {e}")
            raise

    def confirm_invoice(self, draft_id: int) -> Dict[str, Any]:
        """Confirm/validate draft invoice.

        Args:
            draft_id: Odoo invoice ID

        Returns:
            Dict with status info
        """
        if not self.odoo:
            raise RuntimeError("Not connected to Odoo")

        try:
            AccountMove = self.odoo.env['account.move']
            invoice = AccountMove.browse(draft_id)

            # Validate invoice
            invoice.action_post()

            logger.info(f"Confirmed invoice {draft_id}")

            return {
                'draft_id': draft_id,
                'state': 'posted',
                'confirmed': True,
            }

        except Exception as e:
            logger.error(f"Failed to confirm invoice {draft_id}: {e}")
            raise

    def search_invoices(
        self,
        domain: Optional[List] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for invoices (read-only).

        Args:
            domain: Odoo domain filter (e.g., [('state', '=', 'posted')])
            limit: Maximum results to return

        Returns:
            List of invoice records
        """
        if not self.odoo:
            raise RuntimeError("Not connected to Odoo")

        try:
            AccountMove = self.odoo.env['account.move']

            domain = domain or []
            invoice_ids = AccountMove.search(domain, limit=limit)

            # Read invoice data
            invoices = AccountMove.read(
                invoice_ids,
                ['name', 'partner_id', 'amount_total', 'currency_id', 'state', 'invoice_date']
            )

            return invoices

        except Exception as e:
            logger.error(f"Failed to search invoices: {e}")
            raise

    def _get_currency_id(self, currency_code: str) -> int:
        """Get Odoo currency ID from code.

        Args:
            currency_code: ISO currency code (e.g., 'PKR', 'USD')

        Returns:
            Odoo currency ID
        """
        if not self.odoo:
            raise RuntimeError("Not connected to Odoo")

        Currency = self.odoo.env['res.currency']
        currency_ids = Currency.search([('name', '=', currency_code)], limit=1)

        if not currency_ids:
            raise ValueError(f"Currency {currency_code} not found in Odoo")

        return currency_ids[0]

    def get_partner_by_name(self, partner_name: str) -> Optional[int]:
        """Find partner (customer/vendor) by name.

        Args:
            partner_name: Partner name to search

        Returns:
            Partner ID or None if not found
        """
        if not self.odoo:
            raise RuntimeError("Not connected to Odoo")

        try:
            Partner = self.odoo.env['res.partner']
            partner_ids = Partner.search([('name', 'ilike', partner_name)], limit=1)

            return partner_ids[0] if partner_ids else None

        except Exception as e:
            logger.error(f"Failed to search partner: {e}")
            raise

    def close(self):
        """Close Odoo connection."""
        if self.odoo:
            # odoorpc doesn't require explicit close
            self.odoo = None
            logger.info("Odoo connection closed")


# Example usage (for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    try:
        client = OdooClient()

        # Test: Search for partners
        partner_id = client.get_partner_by_name("Test Partner")
        print(f"Found partner ID: {partner_id}")

        # Test: Search invoices
        invoices = client.search_invoices([('state', '=', 'draft')], limit=5)
        print(f"Found {len(invoices)} draft invoices")

        client.close()

    except Exception as e:
        print(f"Test failed: {e}")
