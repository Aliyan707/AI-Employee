#!/usr/bin/env python3
"""Odoo MCP Server - Model Context Protocol server for Odoo ERP integration.

Provides MCP tools for Gold-tier AI Employee to interact with Odoo Community 19+
for automated invoice/payment drafting, confirmation, posting, and audit data collection.

Protocol: stdio (reads JSON-RPC from stdin, writes to stdout)
"""

import sys
import json
import logging
from typing import Dict, Any, List
from pathlib import Path

from odoo_client import OdooClient

# Setup logging (to stderr to avoid interfering with stdio protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class OdooMCPServer:
    """MCP Server for Odoo ERP integration."""

    def __init__(self):
        """Initialize MCP server."""
        self.client: OdooClient = None
        self.tools = {
            'odoo_create_draft_invoice': self.create_draft_invoice,
            'odoo_confirm_invoice': self.confirm_invoice,
            'odoo_post_invoice': self.post_invoice,
            'odoo_search_invoices': self.search_invoices,
        }

        try:
            self.client = OdooClient()
            logger.info("Odoo MCP Server initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Odoo client: {e}")
            raise

    def create_draft_invoice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """MCP tool: Create draft invoice in Odoo.

        Args:
            params: {
                'partner_name': str,  # Customer name (will search for ID)
                'amount': float,      # Invoice amount
                'currency': str,      # Currency code (default: PKR)
                'description': str,   # Invoice description
                'invoice_date': str   # Optional: YYYY-MM-DD
            }

        Returns:
            Draft invoice details
        """
        try:
            partner_name = params['partner_name']
            amount = params['amount']
            currency = params.get('currency', 'PKR')
            description = params.get('description', '')
            invoice_date = params.get('invoice_date')

            # Find partner ID
            partner_id = self.client.get_partner_by_name(partner_name)
            if not partner_id:
                return {
                    'success': False,
                    'error': f"Partner '{partner_name}' not found in Odoo"
                }

            # Create draft invoice
            result = self.client.create_draft_invoice(
                partner_id=partner_id,
                amount=amount,
                currency=currency,
                description=description,
                invoice_date=invoice_date
            )

            return {
                'success': True,
                'draft_id': result['draft_id'],
                'state': result['state'],
                'partner_name': partner_name,
                'amount': amount,
                'currency': currency,
                'message': f"Draft invoice {result['draft_id']} created for {partner_name}"
            }

        except Exception as e:
            logger.error(f"create_draft_invoice failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def confirm_invoice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """MCP tool: Confirm/validate draft invoice.

        Args:
            params: {
                'draft_id': int,      # Odoo invoice ID
                'approval_file': str  # Path to approval file (MUST exist in Approved/)
            }

        Returns:
            Confirmation status
        """
        try:
            draft_id = params['draft_id']
            approval_file = params.get('approval_file')

            # CONSTITUTIONAL SAFETY CHECK
            if not approval_file:
                return {
                    'success': False,
                    'error': 'CONSTITUTIONAL VIOLATION: approval_file required for confirm operation'
                }

            # Verify approval file exists
            if not Path(approval_file).exists():
                return {
                    'success': False,
                    'error': f'Approval file not found: {approval_file}'
                }

            # Verify file is in Approved/ folder
            if '/Approved/' not in str(approval_file) and '\\Approved\\' not in str(approval_file):
                return {
                    'success': False,
                    'error': f'CONSTITUTIONAL VIOLATION: File must be in Approved/ folder, got: {approval_file}'
                }

            # Confirm invoice
            result = self.client.confirm_invoice(draft_id)

            return {
                'success': True,
                'draft_id': draft_id,
                'state': result['state'],
                'confirmed': result['confirmed'],
                'message': f"Invoice {draft_id} confirmed successfully"
            }

        except Exception as e:
            logger.error(f"confirm_invoice failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def post_invoice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """MCP tool: Post invoice to ledger (same as confirm for Odoo invoices).

        Args:
            params: {
                'draft_id': int,      # Odoo invoice ID
                'approval_file': str  # Path to approval file (MUST exist in Approved/)
            }

        Returns:
            Posting status
        """
        # In Odoo, confirm and post are often the same action (action_post)
        # So we delegate to confirm_invoice
        return self.confirm_invoice(params)

    def search_invoices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """MCP tool: Search invoices (read-only, no approval needed).

        Args:
            params: {
                'state': str,        # Optional: 'draft', 'posted', etc.
                'date_from': str,    # Optional: YYYY-MM-DD
                'date_to': str,      # Optional: YYYY-MM-DD
                'limit': int         # Optional: max results (default 100)
            }

        Returns:
            List of invoices
        """
        try:
            state = params.get('state')
            limit = params.get('limit', 100)

            # Build Odoo domain filter
            domain = []
            if state:
                domain.append(('state', '=', state))

            # Search invoices
            invoices = self.client.search_invoices(domain=domain, limit=limit)

            return {
                'success': True,
                'count': len(invoices),
                'invoices': invoices,
                'message': f"Found {len(invoices)} invoices"
            }

        except Exception as e:
            logger.error(f"search_invoices failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool call request.

        Args:
            request: JSON-RPC request

        Returns:
            JSON-RPC response
        """
        try:
            tool_name = request.get('method')
            params = request.get('params', {})
            request_id = request.get('id')

            if tool_name not in self.tools:
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Tool not found: {tool_name}'
                    }
                }

            # Execute tool
            result = self.tools[tool_name](params)

            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': result
            }

        except Exception as e:
            logger.error(f"Request handling failed: {e}")
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {
                    'code': -32603,
                    'message': str(e)
                }
            }

    def run(self):
        """Run MCP server (stdio protocol).

        Reads JSON-RPC requests from stdin, writes responses to stdout.
        """
        logger.info("Odoo MCP Server started (stdio mode)")

        try:
            for line in sys.stdin:
                if not line.strip():
                    continue

                try:
                    request = json.loads(line)
                    response = self.handle_request(request)

                    # Write response to stdout
                    print(json.dumps(response), flush=True)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        'jsonrpc': '2.0',
                        'id': None,
                        'error': {
                            'code': -32700,
                            'message': 'Parse error'
                        }
                    }
                    print(json.dumps(error_response), flush=True)

        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            if self.client:
                self.client.close()
            logger.info("Odoo MCP Server stopped")


if __name__ == '__main__':
    server = OdooMCPServer()
    server.run()
