# Silver-Tier AI Employee - Watchers

Perception layer for the Silver-tier Personal AI Employee system. These Python scripts continuously monitor external sources and create actionable files in the Obsidian vault for Claude Code to process.

## Architecture

```
External Sources → Watchers → Vault/Needs_Action/ → Claude Code
```

## Available Watchers

### 1. Gmail Watcher (`gmail_watcher.py`)
- **Monitors**: Gmail inbox for important/unread messages
- **Creates**: `EMAIL_*.md` files in `Needs_Action/Email/`
- **Check Interval**: 120 seconds (2 minutes)
- **Prerequisites**: Gmail API credentials

### 2. File System Watcher (`filesystem_watcher.py`)
- **Monitors**: Designated drop folder for new files
- **Creates**: `FILE_*.md` metadata files in `Needs_Action/`
- **Mode**: Event-driven (real-time)
- **Prerequisites**: Drop folder path

## Installation

### 1. Install Dependencies

```bash
cd watchers
pip install -r requirements.txt
```

### 2. Configure Gmail API (for Gmail Watcher)

#### A. Enable Gmail API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API for the project
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `gmail-credentials.json`

#### B. First-time OAuth Flow
The first time you run the Gmail watcher, it will open a browser for OAuth consent:
1. Sign in with your Google account
2. Grant permissions to read Gmail
3. Token will be saved for future use

### 3. Create Configuration File

```bash
cp config.env.example config.env
# Edit config.env with your paths
```

Example `config.env`:
```bash
VAULT_PATH=/Users/aliyan/AI_Employee_Vault
GMAIL_CREDENTIALS_PATH=/Users/aliyan/.credentials/gmail-credentials.json
DROP_FOLDER_PATH=/Users/aliyan/Desktop/AI_Drop
COPY_FILES_TO_VAULT=true
```

## Usage

### Run Watchers Standalone (Testing)

**Gmail Watcher:**
```bash
python gmail_watcher.py /path/to/vault /path/to/gmail-credentials.json
```

**File System Watcher:**
```bash
python filesystem_watcher.py /path/to/vault /path/to/drop-folder
```

### Run Watchers with Process Manager (Production)

Using PM2 (recommended):

```bash
# Install PM2
npm install -g pm2

# Start Gmail watcher
pm2 start gmail_watcher.py --name gmail-watcher \
  --interpreter python3 \
  -- /path/to/vault /path/to/credentials.json

# Start filesystem watcher
pm2 start filesystem_watcher.py --name file-watcher \
  --interpreter python3 \
  -- /path/to/vault /path/to/drop-folder

# Save configuration for auto-start on reboot
pm2 save
pm2 startup

# Monitor watchers
pm2 list
pm2 logs
```

Using systemd (Linux):

Create `/etc/systemd/system/gmail-watcher.service`:
```ini
[Unit]
Description=Silver-tier AI Employee - Gmail Watcher
After=network.target

[Service]
Type=simple
User=aliyan
WorkingDirectory=/home/aliyan/AI_Employee/watchers
ExecStart=/usr/bin/python3 gmail_watcher.py /home/aliyan/AI_Employee_Vault /home/aliyan/.credentials/gmail-credentials.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable gmail-watcher.service
sudo systemctl start gmail-watcher.service
sudo systemctl status gmail-watcher.service
```

## Output Format

### Email Action File Example

**File**: `Needs_Action/Email/EMAIL_20260215_103045_a1b2c3d4.md`

```markdown
---
type: email
from: client@example.com
subject: Question about AI automation services
received: 2026-02-15T10:30:45+05:00
original_date: Fri, 15 Feb 2026 10:28:12 +0500
priority: high
status: pending
gmail_id: a1b2c3d4e5f6g7h8
---

## Email Preview
Hi Aliyan, I found your profile on LinkedIn and I'm interested in learning more about your AI automation services...

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
- [ ] Flag for human review

## Notes
Created by Gmail Watcher at 2026-02-15T10:30:45+05:00
```

### File Drop Action File Example

**File**: `Needs_Action/FILE_20260215_143022_invoice.md`

```markdown
---
type: file_drop
original_name: invoice-jan-2026.pdf
original_path: /Users/aliyan/Desktop/AI_Drop/invoice-jan-2026.pdf
size_bytes: 245678
file_type: document
copied_to_vault: Files/20260215_143022_invoice-jan-2026.pdf
received: 2026-02-15T14:30:22+05:00
status: pending
---

## File Details
- **Original Name**: invoice-jan-2026.pdf
- **Size**: 239.9 KB
- **Type**: document
- **Dropped**: 2026-02-15T14:30:22+05:00

## Vault Location
File copied to: `Files/20260215_143022_invoice-jan-2026.pdf`

## Suggested Actions
- [ ] Review file content
- [ ] Process or extract information
- [ ] Archive or delete original
- [ ] Update relevant project files

## Notes
Created by FileSystem Watcher
```

## Troubleshooting

### Gmail Watcher Issues

**Problem**: `403 Forbidden` error
- **Solution**: Verify Gmail API is enabled in Google Cloud Console
- **Solution**: Check OAuth consent screen is configured

**Problem**: Token expired
- **Solution**: Delete `gmail_token.pickle` and re-authenticate

**Problem**: No emails detected
- **Solution**: Verify query filter (`is:unread is:important`)
- **Solution**: Check if emails are actually marked as important

### File System Watcher Issues

**Problem**: Files not detected
- **Solution**: Verify drop folder path is correct
- **Solution**: Check file permissions
- **Solution**: Ensure watcher is running (`pm2 list`)

**Problem**: Watcher stops after some time
- **Solution**: Use process manager (PM2/systemd) for auto-restart
- **Solution**: Check logs for errors

### General Issues

**Problem**: Import errors
- **Solution**: Ensure all dependencies installed: `pip install -r requirements.txt`
- **Solution**: Use correct Python version (3.11+)

**Problem**: Permission denied writing to vault
- **Solution**: Check folder permissions
- **Solution**: Ensure vault path is correct

## Architecture Notes

### Base Watcher Pattern
All watchers inherit from `BaseWatcher` class which provides:
- Consistent logging infrastructure
- Error handling and resilience
- Timestamp formatting (PKT timezone)
- Main run loop with interruption handling

### Event-Driven vs Polling
- **Gmail Watcher**: Polling-based (checks every 2 minutes)
- **File System Watcher**: Event-driven (real-time detection via watchdog)

### Integration with Claude Code
Watchers create files → Claude Code processes via:
1. Email Sub-Agent monitors `Needs_Action/Email/`
2. Main Orchestrator monitors `Needs_Action/`
3. Agents use claim-by-move to process files

## Security Considerations

1. **Never commit credentials**:
   - Add `config.env` to `.gitignore`
   - Add `*.json` (credentials) to `.gitignore`
   - Add `*.pickle` (tokens) to `.gitignore`

2. **OAuth token security**:
   - Store `gmail_token.pickle` in secure location
   - Set restrictive permissions: `chmod 600 gmail_token.pickle`

3. **Vault permissions**:
   - Ensure only your user can read/write vault
   - Consider encrypting vault at rest (Obsidian feature)

## Next Steps

After watchers are running:
1. Deploy Claude Code agents (see `System/DEPLOYMENT.md`)
2. Test end-to-end flow (email arrives → agent processes → approval → send)
3. Monitor logs for issues
4. Adjust check intervals based on usage patterns

## Logs

Watchers log to:
- **Console**: Real-time output (if running in terminal)
- **File**: `Vault/Logs/gmail_watcher.log`, `Vault/Logs/filesystem_watcher.log`

View logs with PM2:
```bash
pm2 logs gmail-watcher
pm2 logs file-watcher
```

## Contributing

When adding new watchers:
1. Inherit from `BaseWatcher`
2. Implement `check_for_updates()` and `create_action_file()`
3. Follow naming convention: `<source>_watcher.py`
4. Create action files in appropriate `Needs_Action/` subfolder
5. Update this README with usage instructions
