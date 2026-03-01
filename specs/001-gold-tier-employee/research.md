# Research: Gold-Tier Autonomous AI Employee

**Feature**: 001-gold-tier-employee
**Phase**: 0 (Research & Design Decisions)
**Date**: 2026-02-15

## Purpose

Resolve technical unknowns ("NEEDS CLARIFICATION") from plan.md Technical Context and establish design foundations for Phase 1 (Data Model & Contracts).

## Research Questions & Findings

### 1. Odoo MCP Server Technology Stack

**Question**: What technology stack should be used for custom odoo-mcp server development?

**Options Evaluated**:
1. Python 3.11+ with odoo-rpc + FastAPI + Pydantic
2. Node.js with odoo-xmlrpc + Express
3. Direct XML-RPC without abstraction library

**Decision**: **Python 3.11+ with odoo-rpc + FastAPI + Pydantic**

**Rationale**:
- **Python ecosystem maturity**: `odoo-rpc` library provides high-level Odoo API client with connection pooling, session management, and error handling
- **FastAPI async support**: Native async/await for MCP server implementation. Automatic OpenAPI documentation useful for debugging.
- **Pydantic validation**: Type-safe request/response schemas prevent MCP protocol violations. JSON schema generation for contracts.
- **Community support**: Large Python + Odoo community. Well-documented patterns for Odoo integration.

**Alternatives Rejected**:
- **Node.js**: odoo-xmlrpc library less mature than Python equivalents. Callback-heavy async model more error-prone.
- **Direct XML-RPC**: No connection pooling, session reuse, or high-level error handling. Would require implementing these from scratch.

**References**:
- odoo-rpc docs: https://github.com/acsone/odoo-rpc
- FastAPI MCP examples: https://github.com/anthropics/mcp-examples (Python FastAPI server pattern)
- Pydantic JSON Schema: https://docs.pydantic.dev/latest/usage/json_schema/

---

### 2. Browser MCP Extension Strategy

**Question**: How should existing browser-mcp be extended for LinkedIn, Facebook, Instagram, Twitter/X support?

**Options Evaluated**:
1. Extend browser-mcp with platform-specific selector configs
2. Build separate Puppeteer/Playwright automation (bypass MCP)
3. Use platform APIs (LinkedIn API, Facebook Graph API, etc.)

**Decision**: **Extend browser-mcp with platform-specific selector configs**

**Rationale**:
- **Leverage existing infrastructure**: browser-mcp already handles browser lifecycle, CDP connection, screenshot capture. Only need to add platform workflows.
- **Consistent MCP interface**: All external integrations (email, browser, Odoo) use MCP protocol. Simplifies agent skill invocations.
- **Flexibility for anti-bot measures**: Platform APIs have strict rate limits and require app approval (weeks/months). Browser automation bypasses API restrictions.
- **Multi-platform support**: Single MCP server handles all platforms with platform-specific navigate/fill/click sequences.

**Alternatives Rejected**:
- **Puppeteer/Playwright direct**: Breaks MCP architecture. Agents would need platform-specific code instead of generic MCP calls.
- **Platform APIs**: LinkedIn API requires partnership approval (30-90 days). Facebook Graph API strict rate limits (200 posts/hour). Instagram no official API for posting. Twitter/X API expensive ($100/month for basic access).

**Implementation Notes**:
- Add `social_platforms.json` config to browser-mcp with selectors for each platform (post compose button, text area, image upload, publish button)
- Platform-specific workflows: `navigate(url) → wait(selector) → fill(selector, content) → click(publish) → wait(confirmation)`
- Screenshot capture after each step for debugging/logging

**References**:
- browser-mcp repo: https://github.com/anthropics/mcp-browser (example MCP server)
- LinkedIn posting selectors: Manual exploration (LinkedIn web UI, inspect element)
- Anti-detection best practices: Playwright stealth plugin patterns

---

### 3. Agent Execution Pattern

**Question**: What execution pattern should sub-agents follow for consistency and reliability?

**Options Evaluated**:
1. 5-phase cycle (Observe & Claim → Classify & Delegate → Execute with HITL → Audit & Weekly → Clean, Log & Report)
2. Event-driven webhooks (filesystem watchers trigger agents on file create)
3. Cron-based scheduling (agents run every N minutes on fixed schedule)

**Decision**: **5-phase cycle** (user-provided pattern)

**Rationale**:
- **Standardization**: All sub-agents follow identical pattern. Reduces cognitive load, simplifies debugging.
- **Atomic claiming**: Phase 1 (Observe & Claim) uses atomic file move to prevent race conditions. Clear ownership semantics.
- **Skill delegation**: Phase 2 (Classify & Delegate) routes work to approved skills (odoo-accounting, multi-social-poster, etc.). Maintains modularity.
- **HITL enforcement**: Phase 3 (Execute with HITL) enforces approval gates constitutionally. No bypassing.
- **Audit integration**: Phase 4 (Audit & Weekly) handles special WEEKLY_AUDIT_TRIGGER.md trigger for Sunday night audits.
- **Complete logging**: Phase 5 (Clean, Log & Report) ensures Dashboard.md + Logs/YYYY-MM-DD.jsonl updated after every cycle.

**Alternatives Rejected**:
- **Event-driven webhooks**: Requires filesystem watchers (inotify on Linux, FSEvents on macOS, ReadDirectoryChangesW on Windows). Platform-specific. Adds complexity for Gold-tier local deployment.
- **Cron-based scheduling**: Fixed intervals (every 5 min) waste CPU when no work available. Also misses urgent items until next cycle. On-demand claiming more responsive.

**Cycle Frequency**: On-demand (agents run cycle when triggered by Claude Code agent runtime). No fixed interval polling.

**References**:
- User-provided 5-phase pattern (in /sp.plan input)
- Filesystem atomic move operations: POSIX rename() semantics (atomic on same filesystem)

---

### 4. Logging Format

**Question**: What format should be used for audit logging (Logs/YYYY-MM-DD.jsonl)?

**Options Evaluated**:
1. JSON Lines (.jsonl) - one JSON object per line
2. Structured JSON array (single JSON file with array of log entries)
3. Plain text logs (human-readable, not machine-parseable)
4. SQLite database (structured query support)

**Decision**: **JSON Lines (.jsonl)**

**Rationale**:
- **Line-by-line parseability**: Each line is independent JSON object. Can process with `jq`, `grep`, or stream parsers without loading entire file.
- **Append-only safety**: New log entries appended to end of file. No file rewrite needed (unlike JSON arrays). Safe for concurrent writes from multiple agents.
- **Standard format**: JSON Lines widely supported (logstash, fluentd, jq). Easy integration with log aggregation tools if needed later.
- **Human + machine readable**: JSON is self-documenting (field names in each entry). Pretty-print any line for debugging.

**Alternatives Rejected**:
- **JSON array**: Appending requires reading entire file, parsing JSON array, adding element, rewriting file. Not safe for concurrent writes. File grows linearly in size (O(n) parse time).
- **Plain text logs**: Human-readable but not machine-parseable. Would need regex parsing (fragile). No structured fields for filtering.
- **SQLite**: Over-engineered for Gold-tier local deployment. Requires locking, transaction management, schema migrations. Adds external dependency.

**Schema**: See contracts/logs.schema.json for required fields (timestamp PKT, agent, action, file, status, metadata).

**References**:
- JSON Lines spec: https://jsonlines.org/
- jq examples: https://stedolan.github.io/jq/manual/ (JSON Lines processing)

---

### 5. Vault Coordination Mechanism

**Question**: How should sub-agents coordinate to prevent duplicate processing and ensure exclusive file ownership?

**Options Evaluated**:
1. Atomic file move operations (claim-by-move)
2. File locking (fcntl/flock)
3. Database-backed work queue (PostgreSQL, Redis)
4. Pub/sub messaging (Redis pub/sub, NATS)

**Decision**: **Atomic file move operations (claim-by-move)**

**Rationale**:
- **OS-level atomicity**: Filesystem rename() operation is atomic on same filesystem (POSIX guarantee). First agent to move Needs_Action/file.md to In_Progress/agent/file.md wins. Loser gets ENOENT error and skips.
- **Natural ownership**: File location indicates ownership. In_Progress/accounting-sub-agent/ACCOUNTING_INVOICE_001.md clearly owned by accounting agent. No external state to track.
- **Simple implementation**: No locking primitives, no external services, no coordination protocol. Just move file and check error code.
- **Visible state**: Human can inspect In_Progress/ folders to see which agent owns which files. Dashboard.md shows ownership via recent activity.

**Alternatives Rejected**:
- **File locking**: fcntl(F_SETLK) on Unix, LockFileEx on Windows. Complex deadlock scenarios if agent crashes while holding lock. Lock release on crash not guaranteed. Advisory locks can be bypassed.
- **Database queue**: Requires PostgreSQL or Redis running. Over-engineered for Gold-tier local deployment. Adds external dependency, connection management, transaction overhead.
- **Pub/sub messaging**: Redis pub/sub or NATS requires external service. Adds latency (network round-trip). Over-engineered for local file-based coordination.

**Error Handling**: If file move fails (ENOENT = already claimed), agent logs "file already claimed" and moves to next file. No retry needed.

**References**:
- POSIX rename() atomicity: https://pubs.opengroup.org/onlinepubs/9699919799/functions/rename.html
- Filesystem race condition analysis: https://lwn.net/Articles/325302/

---

### 6. Error Recovery Strategy

**Question**: How should transient vs persistent errors be handled for reliability without infinite retry loops?

**Options Evaluated**:
1. Exponential backoff retry (1min, 5min, 15min) with 3-attempt limit
2. Linear backoff retry (5min intervals, 5 attempts)
3. Circuit breaker pattern (fail fast after N errors in time window)
4. No automatic retry (human intervenes for all errors)

**Decision**: **Exponential backoff retry (1min, 5min, 15min) with 3-attempt limit**

**Rationale**:
- **Transient error recovery**: Network timeouts, temporary service unavailability (Odoo restart, browser glitch) typically resolve within minutes. Exponential backoff gives service time to recover.
- **Prevents thundering herd**: If Odoo is down, all agents don't retry simultaneously (exponential spread). First retry after 1min, second after 5min (total 6min), third after 15min (total 21min).
- **Bounded retry attempts**: 3-attempt limit prevents infinite loops for persistent errors (authentication failure, Odoo misconfiguration). After 3 failures, file moves to Done/ERROR_* and flags in Dashboard.md for human intervention.
- **Clear error classification**: Transient = network timeout, 503 Service Unavailable, connection refused. Persistent = 401 Unauthorized, 404 Not Found, malformed response.

**Alternatives Rejected**:
- **Linear backoff**: 5min fixed interval too aggressive if service down for extended period (e.g., Odoo upgrade takes 30min). Wastes retries early.
- **Circuit breaker**: Complex state machine (closed → open → half-open). Over-engineered for Gold-tier. Designed for distributed systems with thousands of requests/sec.
- **No retry**: Reduces reliability. Many errors are transient (temporary network glitch). Human intervention adds latency (hours until noticed and resolved).

**Error Types & Handling**:
| Error Type | Classification | Retry? | Example |
|------------|----------------|--------|---------|
| Connection timeout | Transient | Yes (3x) | Network glitch, Odoo restarting |
| 503 Service Unavailable | Transient | Yes (3x) | Odoo under load |
| 401 Unauthorized | Persistent | No | Invalid Odoo credentials |
| 404 Not Found | Persistent | No | Odoo record deleted externally |
| Malformed JSON response | Persistent | No | Odoo API version mismatch |
| Rate limit (429) | Transient | Yes (3x) | Odoo rate limit hit |

**References**:
- Exponential backoff best practices: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
- HTTP status codes: https://httpstatuses.com/

---

### 7. Approval Timeout

**Question**: How long should files sit in Pending_Approval/ before assuming rejection?

**Options Evaluated**:
1. 24 hours (assume rejection if not moved to Approved/)
2. No timeout (files sit indefinitely until human acts)
3. 4 hours (business day coverage)
4. 72 hours (weekend + holiday coverage)

**Decision**: **24 hours**

**Rationale**:
- **Business owner availability**: Assumption is business owner reviews Pending_Approval/ folder once per day (morning and afternoon). 24-hour window accommodates single-day delay (busy day, forgot to check).
- **Weekend coverage**: If approval needed Friday evening, 24-hour timeout doesn't trigger until Saturday evening. Business owner has Saturday to review before rejection.
- **Prevents stalled workflows**: Without timeout, forgotten approvals stall indefinitely. File never moves to Done/, blocks future similar work.
- **Configurable in Company_Handbook.md**: If business owner wants longer timeout (e.g., 48 hours for extended trips), can override in Company_Handbook.md.

**Alternatives Rejected**:
- **No timeout**: Workflows can stall indefinitely if business owner forgets or is unavailable. No automatic cleanup.
- **4 hours**: Too aggressive for weekend/holiday coverage. If approval needed Friday 5pm, timeout triggers Friday 9pm (before weekend review).
- **72 hours**: Too lenient. Three-day approval delay defeats purpose of automation (urgent invoice posting).

**Rejection Handling**:
- After 24 hours in Pending_Approval/, agent moves file to Done/REJECTED_[filename]
- Log entry: `{"action":"approval_timeout","file":"ACCOUNTING_INVOICE_001.md","reason":"timeout_no_approval","timeout_hours":24}`
- Dashboard.md updated: Remove from Pending Approvals list, add to Recent Activity: "REJECTED due to timeout"

**References**:
- User expectations: Assumption documented in spec.md (Assumption 9: Human Availability)

---

### 8. Weekly Audit Timing

**Question**: When should weekly audit trigger (Sunday night) and CEO briefing generate (Monday morning)?

**Options Evaluated**:
1. Sunday 23:00 PKT trigger, Monday 07:00 PKT briefing
2. Friday 18:00 PKT trigger, Monday 08:00 PKT briefing
3. Real-time continuous metrics (no weekly cadence)
4. Monday 08:00 PKT trigger + briefing (same time)

**Decision**: **Sunday 23:00 PKT trigger, Monday 07:00 PKT briefing**

**Rationale**:
- **Complete week data**: Sunday night allows full week (Mon-Sun) data collection. Captures weekend work if any.
- **Monday morning readiness**: Briefing generated Monday 07:00 PKT, ready before business day starts (09:00 PKT). CEO has 2 hours to review and plan week.
- **Weekend processing**: Audit runs overnight (Sunday 23:00 - Monday 07:00). Doesn't consume business hours.
- **Configurable timing**: Main Orchestrator can adjust trigger time via Company_Handbook.md (e.g., 22:00 PKT for earlier briefing).

**Alternatives Rejected**:
- **Friday evening audit**: Doesn't capture weekend work. Briefing 3 days old by Monday (stale data).
- **Real-time continuous metrics**: Over-engineered for weekly executive summary. Dashboard.md provides real-time status; briefing is weekly rollup.
- **Same-time trigger + briefing**: Briefing generation would be rushed (no time for audit data collection). Better to separate audit (Sunday night) from briefing (Monday morning).

**Audit Workflow**:
1. **Sunday 23:00 PKT**: Main Orchestrator creates `WEEKLY_AUDIT_TRIGGER.md` in Needs_Action/
2. **Sunday 23:01 PKT**: Finance & Auditor Sub-Agent claims trigger, invokes `weekly-audit-engine` skill
3. **Sunday 23:01 - 23:10 PKT**: Audit data collection (Odoo revenue, bank CSV expenses, Done/ tasks, Social/Summary_* metrics)
4. **Sunday 23:10 PKT**: Write `Accounting/Audit_Data_2026-02-15.md`, log completion
5. **Monday 07:00 PKT**: Finance & Auditor Sub-Agent invokes `ceo-briefing-generator` skill
6. **Monday 07:00 - 07:15 PKT**: Briefing generation (read Business_Goals.md, Audit_Data, Dashboard.md; write Briefings/2026-02-17_Monday_Briefing.md)
7. **Monday 07:15 PKT**: Briefing ready for CEO review

**References**:
- Pakistan business hours: 09:00-18:00 PKT Mon-Fri, 09:00-14:00 PKT Sat (Assumption 8 in spec.md)
- Sunday as week-end day in Pakistani calendar (Friday is holy day but not standard weekend; Sat-Sun more common in business)

---

## Research Conclusions

**All NEEDS CLARIFICATION items resolved.**

**Key Technical Decisions**:
1. Odoo MCP: Python 3.11+ + odoo-rpc + FastAPI + Pydantic
2. Browser MCP: Extend with platform-specific selectors (LinkedIn, FB, IG, X)
3. Agent Pattern: 5-phase cycle (Observe & Claim → Classify & Delegate → Execute with HITL → Audit & Weekly → Clean, Log & Report)
4. Logging: JSON Lines (.jsonl) format
5. Coordination: Atomic file move operations (claim-by-move)
6. Error Recovery: Exponential backoff (1min, 5min, 15min), 3-attempt limit
7. Approval Timeout: 24 hours (assume rejection)
8. Audit Timing: Sunday 23:00 PKT → Monday 07:00 PKT

**Ready for Phase 1**: Data Model & Contracts (entities, schemas, API definitions)

**No Blockers**: All research questions answered with rationale and references.
