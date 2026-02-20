# Odoo MCP Server

**Purpose:** Model Context Protocol server for Odoo ERP Community 19+ integration via JSON-RPC API

**Version:** 1.0.0
**Protocol:** MCP (Model Context Protocol)
**Integration:** Odoo Community Edition 19+
**API:** Odoo JSON-RPC External API

---

## Features

- **Draft Creation:** Create draft invoices, payments, journal entries in Odoo
- **Confirmation:** Confirm/validate Odoo drafts (requires approval)
- **Posting:** Post records to ledger (requires approval)
- **Search/Read:** Read-only queries for audit data collection (no approval needed)

---

## Prerequisites

1. **Odoo Community 19+ instance** (local or VM) accessible via HTTP/HTTPS
2. **Odoo JSON-RPC API enabled** (default in Community Edition)
3. **Odoo user credentials** with accounting permissions
4. **Python 3.9+** with odoo-rpc library

---

## Installation

```bash
cd mcp-servers/odoo-mcp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Configuration

Create `.env` file in this directory:

```env
ODOO_URL=http://localhost:8069
ODOO_DB=your_database_name
ODOO_USERNAME=your_odoo_username
ODOO_PASSWORD_FILE=/path/to/password_file.txt
```

**Security:** Never commit `.env` file or password files to git!

---

## Usage

### Start MCP Server

```bash
python server.py
```

### MCP Tools Available

1. **odoo_create_draft** - Create draft invoice/payment/journal entry
2. **odoo_confirm** - Confirm/validate draft (requires approval file)
3. **odoo_post** - Post to ledger (requires approval file)
4. **odoo_search_records** - Read-only search for audit data

---

## Architecture

```
odoo-mcp/
├── server.py              # MCP server main (stdio protocol)
├── odoo_client.py         # Odoo JSON-RPC client wrapper
├── methods/               # MCP tool implementations
│   ├── create_draft.py    # Draft creation logic
│   ├── confirm.py         # Confirm/validate logic
│   ├── post.py            # Post to ledger logic
│   └── search_records.py  # Read-only search logic
├── config.json            # MCP server configuration
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## Integration with Claude Code

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "odoo",
      "command": "python",
      "args": ["/absolute/path/to/mcp-servers/odoo-mcp/server.py"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "your_database",
        "ODOO_USERNAME": "your_username",
        "ODOO_PASSWORD_FILE": "/path/to/password.txt"
      }
    }
  ]
}
```

---

## Safety & Approval Workflow

**CRITICAL:** All state-changing operations (confirm, post) require:
1. Approved file exists in `Approved/` folder
2. File contains complete payload
3. Timestamp <24 hours
4. No constitutional violations

Read-only operations (search_records) do NOT require approval.

---

## Testing

Test with sample Odoo Community 19+ instance:

```bash
# Create draft invoice
python -c "from odoo_client import OdooClient; client = OdooClient(); print(client.create_draft_invoice('Partner Name', 50000, 'PKR', 'Test invoice'))"
```

---

## Odoo JSON-RPC References

- [Odoo 19 External API Documentation](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- [Odoo RPC Library](https://github.com/OCA/odoorpc)

---

**Status:** 🔧 Implementation in progress (Gold-tier requirement)
