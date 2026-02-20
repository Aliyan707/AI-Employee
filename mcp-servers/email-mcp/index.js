#!/usr/bin/env node

/**
 * Email MCP Server for Silver-tier AI Employee
 *
 * Provides email sending capabilities via Gmail API for approved email drafts.
 * Integrates with vault-based HITL approval workflow.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { google } from 'googleapis';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const VAULT_PATH = process.env.VAULT_PATH || path.join(process.cwd(), '..', '..');
const GMAIL_CREDENTIALS_PATH = process.env.GMAIL_CREDENTIALS_PATH;
const GMAIL_TOKEN_PATH = process.env.GMAIL_TOKEN_PATH;

// Gmail API setup
let gmail = null;
let auth = null;

/**
 * Initialize Gmail API authentication
 */
async function initGmailAuth() {
  try {
    // Load credentials
    const credentials = JSON.parse(
      await fs.readFile(GMAIL_CREDENTIALS_PATH, 'utf-8')
    );

    const { client_secret, client_id, redirect_uris } = credentials.installed || credentials.web;

    // Create OAuth2 client
    const oAuth2Client = new google.auth.OAuth2(
      client_id,
      client_secret,
      redirect_uris[0]
    );

    // Load token if exists
    try {
      const token = JSON.parse(await fs.readFile(GMAIL_TOKEN_PATH, 'utf-8'));
      oAuth2Client.setCredentials(token);
    } catch (error) {
      console.error('No valid token found. Please run authentication flow first.');
      throw new Error('Gmail authentication required. Run gmail_watcher.py first to authenticate.');
    }

    auth = oAuth2Client;
    gmail = google.gmail({ version: 'v1', auth: oAuth2Client });

    console.log('[email-mcp] Gmail API initialized successfully');
    return true;
  } catch (error) {
    console.error('[email-mcp] Failed to initialize Gmail API:', error.message);
    throw error;
  }
}

/**
 * Parse email file frontmatter and body
 */
async function parseEmailFile(filePath) {
  const content = await fs.readFile(filePath, 'utf-8');

  // Extract YAML frontmatter
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!frontmatterMatch) {
    throw new Error('Invalid email file format: missing frontmatter');
  }

  const frontmatter = {};
  const yamlContent = frontmatterMatch[1];
  const body = frontmatterMatch[2].trim();

  // Simple YAML parser for key-value pairs
  yamlContent.split('\n').forEach(line => {
    const match = line.match(/^(\w+):\s*(.+)$/);
    if (match) {
      frontmatter[match[1]] = match[2];
    }
  });

  return { frontmatter, body };
}

/**
 * Validate pre-execution checklist
 */
async function validatePreExecution(filePath) {
  const errors = [];

  // Check file exists
  try {
    await fs.access(filePath);
  } catch {
    errors.push('File does not exist');
    return { valid: false, errors };
  }

  // Check file is in Approved/ folder
  if (!filePath.includes('/Approved/') && !filePath.includes('\\Approved\\')) {
    errors.push('File must be in Approved/ folder');
  }

  // Parse file and validate fields
  try {
    const { frontmatter, body } = await parseEmailFile(filePath);

    if (!frontmatter.to) errors.push('Missing required field: to');
    if (!frontmatter.subject) errors.push('Missing required field: subject');
    if (!frontmatter.from) errors.push('Missing required field: from');
    if (!body) errors.push('Missing email body');

    // Check approval timestamp (must be <24 hours old)
    if (frontmatter.timestamp) {
      const approvalTime = new Date(frontmatter.timestamp);
      const now = new Date();
      const hoursSinceApproval = (now - approvalTime) / (1000 * 60 * 60);

      if (hoursSinceApproval > 24) {
        errors.push(`Approval expired (${Math.floor(hoursSinceApproval)} hours old, max 24)`);
      }
    }

    // Check for error flags
    if (body.includes('ERROR:') || frontmatter.error) {
      errors.push('File contains error flag');
    }

  } catch (error) {
    errors.push(`Failed to parse file: ${error.message}`);
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Send email via Gmail API
 */
async function sendEmail(to, subject, body, from) {
  if (!gmail) {
    throw new Error('Gmail API not initialized');
  }

  // Create email in RFC 2822 format
  const email = [
    `From: ${from}`,
    `To: ${to}`,
    `Subject: ${subject}`,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=utf-8',
    '',
    body
  ].join('\n');

  // Encode email in base64url
  const encodedEmail = Buffer.from(email)
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');

  // Send via Gmail API
  const response = await gmail.users.messages.send({
    userId: 'me',
    requestBody: {
      raw: encodedEmail
    }
  });

  return response.data;
}

/**
 * Move file from source to destination
 */
async function moveFile(sourcePath, destPath) {
  await fs.rename(sourcePath, destPath);
}

/**
 * Append to log file
 */
async function appendLog(logPath, entry) {
  const logLine = JSON.stringify(entry) + '\n';
  await fs.appendFile(logPath, logLine);
}

/**
 * Update Dashboard.md with recent activity
 */
async function updateDashboard(vaultPath, message) {
  const dashboardPath = path.join(vaultPath, 'Dashboard.md');
  const timestamp = new Date().toISOString();
  const pktTime = new Date(timestamp).toLocaleString('en-US', {
    timeZone: 'Asia/Karachi',
    hour12: false
  });

  const activityLine = `- ${pktTime} PKT: ${message}\n`;

  // Read current dashboard
  let content = '';
  try {
    content = await fs.readFile(dashboardPath, 'utf-8');
  } catch {
    // Dashboard doesn't exist, will be created
  }

  // Find Recent Activity section or create it
  if (content.includes('## Recent Activity')) {
    // Insert after "## Recent Activity" line
    content = content.replace(
      /(## Recent Activity\n)/,
      `$1${activityLine}`
    );
  } else {
    // Append new section
    content += `\n## Recent Activity\n${activityLine}`;
  }

  await fs.writeFile(dashboardPath, content);
}

/**
 * Handle email send operation (main MCP tool)
 */
async function handleSendEmail(args) {
  const { file_path } = args;

  if (!file_path) {
    throw new Error('Missing required parameter: file_path');
  }

  const absolutePath = path.isAbsolute(file_path)
    ? file_path
    : path.join(VAULT_PATH, file_path);

  console.log(`[email-mcp] Processing email send request: ${absolutePath}`);

  // Step 1: Validate pre-execution checklist
  const validation = await validatePreExecution(absolutePath);
  if (!validation.valid) {
    const error = `Pre-execution validation failed:\n${validation.errors.join('\n')}`;
    console.error(`[email-mcp] ${error}`);

    // Move back to Pending_Approval with error note
    const fileName = path.basename(absolutePath);
    const pendingPath = path.join(VAULT_PATH, 'Pending_Approval', fileName);

    try {
      await moveFile(absolutePath, pendingPath);

      // Append error to file
      const errorNote = `\n\n## ERROR (email-mcp)\n${error}\nTimestamp: ${new Date().toISOString()}\n`;
      await fs.appendFile(pendingPath, errorNote);

      // Log error
      const logPath = path.join(VAULT_PATH, 'Logs', `${new Date().toISOString().split('T')[0]}.md`);
      await appendLog(logPath, {
        timestamp: new Date().toISOString(),
        agent: 'email-mcp',
        action: 'send_email',
        file: fileName,
        status: 'error',
        metadata: {
          error: error,
          validation_errors: validation.errors
        }
      });

      // Update dashboard
      await updateDashboard(VAULT_PATH, `[ERROR] Email send failed: ${fileName} - ${validation.errors[0]}`);
    } catch (moveError) {
      console.error(`[email-mcp] Failed to move file back to Pending_Approval: ${moveError.message}`);
    }

    throw new Error(error);
  }

  // Step 2: Parse email file
  const { frontmatter, body } = await parseEmailFile(absolutePath);
  const { to, subject, from } = frontmatter;

  console.log(`[email-mcp] Sending email to ${to} with subject "${subject}"`);

  try {
    // Step 3: Send email via Gmail API
    const result = await sendEmail(to, subject, body, from);

    console.log(`[email-mcp] Email sent successfully (Message ID: ${result.id})`);

    // Step 4: Success handling
    const fileName = path.basename(absolutePath);
    const sentFileName = `SENT_${fileName}`;
    const donePath = path.join(VAULT_PATH, 'Done', 'Email', sentFileName);

    // Ensure Done/Email directory exists
    await fs.mkdir(path.join(VAULT_PATH, 'Done', 'Email'), { recursive: true });

    // Move to Done/Email/
    await moveFile(absolutePath, donePath);

    // Log success
    const logPath = path.join(VAULT_PATH, 'Logs', `${new Date().toISOString().split('T')[0]}.md`);
    await appendLog(logPath, {
      timestamp: new Date().toISOString(),
      agent: 'email-mcp',
      action: 'send_email',
      file: fileName,
      status: 'completed',
      metadata: {
        to,
        subject,
        message_id: result.id,
        result: 'success'
      }
    });

    // Update Dashboard.md
    await updateDashboard(VAULT_PATH, `[SENT] Email to ${to}: "${subject}"`);

    return {
      success: true,
      message: `Email sent successfully to ${to}`,
      message_id: result.id,
      moved_to: donePath
    };

  } catch (error) {
    console.error(`[email-mcp] Failed to send email: ${error.message}`);

    // Step 5: Failure handling
    const fileName = path.basename(absolutePath);
    const pendingPath = path.join(VAULT_PATH, 'Pending_Approval', fileName);

    // Move back to Pending_Approval with error note
    await moveFile(absolutePath, pendingPath);

    const errorNote = `\n\n## ERROR (email-mcp)\nFailed to send email: ${error.message}\nTimestamp: ${new Date().toISOString()}\n`;
    await fs.appendFile(pendingPath, errorNote);

    // Log error
    const logPath = path.join(VAULT_PATH, 'Logs', `${new Date().toISOString().split('T')[0]}.md`);
    await appendLog(logPath, {
      timestamp: new Date().toISOString(),
      agent: 'email-mcp',
      action: 'send_email',
      file: fileName,
      status: 'error',
      metadata: {
        to,
        subject,
        error: error.message
      }
    });

    // Update Dashboard with error flag
    await updateDashboard(VAULT_PATH, `[ERROR] Failed to send email to ${to}: ${error.message}`);

    throw error;
  }
}

/**
 * Main MCP server setup
 */
async function main() {
  console.log('[email-mcp] Starting email MCP server...');

  // Initialize Gmail API
  await initGmailAuth();

  // Create MCP server
  const server = new Server(
    {
      name: 'email-mcp',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Register send_email tool
  server.setRequestHandler('tools/list', async () => {
    return {
      tools: [
        {
          name: 'send_email',
          description: 'Send an approved email via Gmail API. Requires email draft file in Approved/ folder with frontmatter (to, from, subject) and body content.',
          inputSchema: {
            type: 'object',
            properties: {
              file_path: {
                type: 'string',
                description: 'Path to approved email file (relative to vault or absolute)',
              },
            },
            required: ['file_path'],
          },
        },
      ],
    };
  });

  // Register tool call handler
  server.setRequestHandler('tools/call', async (request) => {
    if (request.params.name === 'send_email') {
      const result = await handleSendEmail(request.params.arguments);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    }

    throw new Error(`Unknown tool: ${request.params.name}`);
  });

  // Start server with stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.log('[email-mcp] Server ready and listening for requests');
}

// Run server
main().catch((error) => {
  console.error('[email-mcp] Fatal error:', error);
  process.exit(1);
});
