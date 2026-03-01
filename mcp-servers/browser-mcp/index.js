#!/usr/bin/env node

/**
 * Browser MCP Server for Silver-tier AI Employee
 *
 * Provides LinkedIn posting capabilities via Playwright browser automation.
 * Integrates with vault-based HITL approval workflow.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { chromium } from 'playwright';
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
const LINKEDIN_EMAIL = process.env.LINKEDIN_EMAIL;
const LINKEDIN_PASSWORD = process.env.LINKEDIN_PASSWORD;
const LINKEDIN_SESSION_PATH = process.env.LINKEDIN_SESSION_PATH || path.join(__dirname, 'linkedin-session');
const HEADLESS = process.env.HEADLESS === 'true';
const BROWSER_TIMEOUT = parseInt(process.env.BROWSER_TIMEOUT || '30000');

// Browser context
let browser = null;
let context = null;
let page = null;

/**
 * Initialize browser with persistent session
 */
async function initBrowser() {
  try {
    console.log('[browser-mcp] Initializing browser...');

    // Launch browser with persistent context (saves login session)
    context = await chromium.launchPersistentContext(LINKEDIN_SESSION_PATH, {
      headless: HEADLESS,
      viewport: { width: 1280, height: 720 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      locale: 'en-US',
      timezoneId: 'Asia/Karachi',
    });

    page = await context.newPage();
    page.setDefaultTimeout(BROWSER_TIMEOUT);

    console.log('[browser-mcp] Browser initialized successfully');
    return true;
  } catch (error) {
    console.error('[browser-mcp] Failed to initialize browser:', error.message);
    throw error;
  }
}

/**
 * Check if logged into LinkedIn
 */
async function isLoggedIn() {
  try {
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    // Check if we're on the feed (logged in) or login page
    const url = page.url();
    return url.includes('/feed/') || url.includes('/in/');
  } catch (error) {
    return false;
  }
}

/**
 * Login to LinkedIn
 */
async function loginToLinkedIn() {
  try {
    console.log('[browser-mcp] Logging into LinkedIn...');

    await page.goto('https://www.linkedin.com/login', { waitUntil: 'domcontentloaded' });

    // Fill login form
    await page.fill('input[name="session_key"]', LINKEDIN_EMAIL);
    await page.fill('input[name="session_password"]', LINKEDIN_PASSWORD);

    // Click login button
    await page.click('button[type="submit"]');

    // Wait for navigation
    await page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: BROWSER_TIMEOUT });

    // Verify login success
    const loggedIn = await isLoggedIn();
    if (!loggedIn) {
      throw new Error('Login failed - check credentials or 2FA requirement');
    }

    console.log('[browser-mcp] Login successful');
    return true;
  } catch (error) {
    console.error('[browser-mcp] Login failed:', error.message);
    throw error;
  }
}

/**
 * Ensure LinkedIn session is active
 */
async function ensureLinkedInSession() {
  if (!page) {
    await initBrowser();
  }

  const loggedIn = await isLoggedIn();
  if (!loggedIn) {
    await loginToLinkedIn();
  }
}

/**
 * Parse LinkedIn post file
 */
async function parsePostFile(filePath) {
  const content = await fs.readFile(filePath, 'utf-8');

  // Extract YAML frontmatter
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!frontmatterMatch) {
    throw new Error('Invalid post file format: missing frontmatter');
  }

  const frontmatter = {};
  const yamlContent = frontmatterMatch[1];
  const body = frontmatterMatch[2].trim();

  // Simple YAML parser
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

  // Parse file and validate
  try {
    const { frontmatter, body } = await parsePostFile(filePath);

    if (!frontmatter.platform || frontmatter.platform !== 'linkedin') {
      errors.push('Platform must be "linkedin"');
    }

    if (!body) {
      errors.push('Missing post content');
    }

    // Validate content length (100-250 words)
    const wordCount = body.trim().split(/\s+/).length;
    if (wordCount < 100) {
      errors.push(`Content too short (${wordCount} words, minimum 100)`);
    }
    if (wordCount > 250) {
      errors.push(`Content too long (${wordCount} words, maximum 250)`);
    }

    // Check for hashtags
    if (!body.includes('#')) {
      errors.push('Missing required hashtags');
    }

    // Check approval timestamp
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
 * Post to LinkedIn
 */
async function postToLinkedIn(content) {
  try {
    console.log('[browser-mcp] Posting to LinkedIn...');

    // Ensure logged in
    await ensureLinkedInSession();

    // Navigate to LinkedIn feed
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);

    // Click "Start a post" button
    const startPostSelector = 'button[aria-label*="Start a post"]';
    await page.waitForSelector(startPostSelector, { timeout: BROWSER_TIMEOUT });
    await page.click(startPostSelector);

    // Wait for post editor to appear
    await page.waitForTimeout(1000);

    // Find and fill the post content area
    const editorSelector = 'div[role="textbox"][aria-label*="share"]';
    await page.waitForSelector(editorSelector, { timeout: BROWSER_TIMEOUT });

    // Click to focus
    await page.click(editorSelector);
    await page.waitForTimeout(500);

    // Type content
    await page.fill(editorSelector, content);
    await page.waitForTimeout(1000);

    // Click Post button
    const postButtonSelector = 'button[aria-label*="Post"]';
    await page.waitForSelector(postButtonSelector, { timeout: BROWSER_TIMEOUT });

    // Wait a moment before clicking post
    await page.waitForTimeout(500);
    await page.click(postButtonSelector);

    // Wait for post to be published
    await page.waitForTimeout(3000);

    // Verify post was published (check for success message or return to feed)
    const url = page.url();
    if (!url.includes('/feed/')) {
      throw new Error('Post may not have been published - unexpected URL after posting');
    }

    console.log('[browser-mcp] Post published successfully');
    return {
      success: true,
      url: url
    };

  } catch (error) {
    console.error('[browser-mcp] Failed to post to LinkedIn:', error.message);
    throw error;
  }
}

/**
 * Move file
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
 * Update Dashboard.md
 */
async function updateDashboard(vaultPath, message) {
  const dashboardPath = path.join(vaultPath, 'Dashboard.md');
  const timestamp = new Date().toISOString();
  const pktTime = new Date(timestamp).toLocaleString('en-US', {
    timeZone: 'Asia/Karachi',
    hour12: false
  });

  const activityLine = `- ${pktTime} PKT: ${message}\n`;

  let content = '';
  try {
    content = await fs.readFile(dashboardPath, 'utf-8');
  } catch {
    // Dashboard doesn't exist
  }

  if (content.includes('## Recent Activity')) {
    content = content.replace(
      /(## Recent Activity\n)/,
      `$1${activityLine}`
    );
  } else {
    content += `\n## Recent Activity\n${activityLine}`;
  }

  await fs.writeFile(dashboardPath, content);
}

/**
 * Handle post_to_linkedin operation (main MCP tool)
 */
async function handlePostToLinkedIn(args) {
  const { file_path } = args;

  if (!file_path) {
    throw new Error('Missing required parameter: file_path');
  }

  const absolutePath = path.isAbsolute(file_path)
    ? file_path
    : path.join(VAULT_PATH, file_path);

  console.log(`[browser-mcp] Processing LinkedIn post request: ${absolutePath}`);

  // Step 1: Validate pre-execution checklist
  const validation = await validatePreExecution(absolutePath);
  if (!validation.valid) {
    const error = `Pre-execution validation failed:\n${validation.errors.join('\n')}`;
    console.error(`[browser-mcp] ${error}`);

    // Move back to Pending_Approval with error
    const fileName = path.basename(absolutePath);
    const pendingPath = path.join(VAULT_PATH, 'Pending_Approval', fileName);

    try {
      await moveFile(absolutePath, pendingPath);

      const errorNote = `\n\n## ERROR (browser-mcp)\n${error}\nTimestamp: ${new Date().toISOString()}\n`;
      await fs.appendFile(pendingPath, errorNote);

      const logPath = path.join(VAULT_PATH, 'Logs', `${new Date().toISOString().split('T')[0]}.md`);
      await appendLog(logPath, {
        timestamp: new Date().toISOString(),
        agent: 'browser-mcp',
        action: 'post_to_linkedin',
        file: fileName,
        status: 'error',
        metadata: {
          error: error,
          validation_errors: validation.errors
        }
      });

      await updateDashboard(VAULT_PATH, `[ERROR] LinkedIn post failed: ${fileName} - ${validation.errors[0]}`);
    } catch (moveError) {
      console.error(`[browser-mcp] Failed to move file back: ${moveError.message}`);
    }

    throw new Error(error);
  }

  // Step 2: Parse post file
  const { frontmatter, body } = await parsePostFile(absolutePath);

  console.log(`[browser-mcp] Posting to LinkedIn...`);

  try {
    // Step 3: Post to LinkedIn
    const result = await postToLinkedIn(body);

    console.log(`[browser-mcp] Post published successfully`);

    // Step 4: Success handling
    const fileName = path.basename(absolutePath);
    const postedFileName = `POSTED_${fileName}`;
    const donePath = path.join(VAULT_PATH, 'Done', 'Social', postedFileName);

    // Ensure Done/Social directory exists
    await fs.mkdir(path.join(VAULT_PATH, 'Done', 'Social'), { recursive: true });

    // Move to Done/Social/
    await moveFile(absolutePath, donePath);

    // Log success
    const logPath = path.join(VAULT_PATH, 'Logs', `${new Date().toISOString().split('T')[0]}.md`);
    await appendLog(logPath, {
      timestamp: new Date().toISOString(),
      agent: 'browser-mcp',
      action: 'post_to_linkedin',
      file: fileName,
      status: 'completed',
      metadata: {
        platform: 'linkedin',
        word_count: body.trim().split(/\s+/).length,
        result: 'success'
      }
    });

    // Update Dashboard
    await updateDashboard(VAULT_PATH, `[POSTED] LinkedIn post published successfully`);

    return {
      success: true,
      message: 'LinkedIn post published successfully',
      moved_to: donePath
    };

  } catch (error) {
    console.error(`[browser-mcp] Failed to post to LinkedIn: ${error.message}`);

    // Step 5: Failure handling
    const fileName = path.basename(absolutePath);
    const pendingPath = path.join(VAULT_PATH, 'Pending_Approval', fileName);

    await moveFile(absolutePath, pendingPath);

    const errorNote = `\n\n## ERROR (browser-mcp)\nFailed to post to LinkedIn: ${error.message}\nTimestamp: ${new Date().toISOString()}\n`;
    await fs.appendFile(pendingPath, errorNote);

    const logPath = path.join(VAULT_PATH, 'Logs', `${new Date().toISOString().split('T')[0]}.md`);
    await appendLog(logPath, {
      timestamp: new Date().toISOString(),
      agent: 'browser-mcp',
      action: 'post_to_linkedin',
      file: fileName,
      status: 'error',
      metadata: {
        platform: 'linkedin',
        error: error.message
      }
    });

    await updateDashboard(VAULT_PATH, `[ERROR] Failed to post to LinkedIn: ${error.message}`);

    throw error;
  }
}

/**
 * Main MCP server setup
 */
async function main() {
  console.log('[browser-mcp] Starting browser MCP server...');

  // Initialize browser
  await initBrowser();

  // Create MCP server
  const server = new Server(
    {
      name: 'browser-mcp',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Register post_to_linkedin tool
  server.setRequestHandler('tools/list', async () => {
    return {
      tools: [
        {
          name: 'post_to_linkedin',
          description: 'Post approved content to LinkedIn via Playwright browser automation. Requires post file in Approved/ folder with platform: linkedin, content (100-250 words), and hashtags.',
          inputSchema: {
            type: 'object',
            properties: {
              file_path: {
                type: 'string',
                description: 'Path to approved LinkedIn post file (relative to vault or absolute)',
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
    if (request.params.name === 'post_to_linkedin') {
      const result = await handlePostToLinkedIn(request.params.arguments);
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

  console.log('[browser-mcp] Server ready and listening for requests');
}

// Cleanup on exit
process.on('SIGINT', async () => {
  console.log('\n[browser-mcp] Shutting down...');
  if (context) {
    await context.close();
  }
  process.exit(0);
});

// Run server
main().catch((error) => {
  console.error('[browser-mcp] Fatal error:', error);
  process.exit(1);
});
