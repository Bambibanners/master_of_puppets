# Phase 1: Output Capture - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Every job execution produces a durable, queryable output record stored server-side. Users can view captured stdout/stderr in a dedicated full-screen log viewer from the dashboard. Security failures (signing rejection, revoked cert) are also recorded as execution history with a distinct status.

Creating, editing, or filtering execution history is Phase 3. Retry logic is Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Log viewer presentation
- Full-screen modal/page (not the existing side panel) — opens when user clicks a job execution
- Single interleaved stream: stdout and stderr in chronological order
- Colour coding: stdout in white/grey, stderr in amber/red
- Prefix labels on every line: `[OUT]` for stdout, `[ERR]` for stderr
- Exit code displayed in **both** places: header metadata (alongside node/duration/timestamp) AND a visual indicator (✔ green / ✘ red) at the end of the log stream

### Per-line timestamps
- Node captures stdout and stderr with per-line timestamps to enable true chronological interleaving
- Each log entry: `{t: <ISO timestamp>, stream: "stdout"|"stderr", line: "<text>"}`
- Client renders in timestamp order — no client-side guessing at interleave order

### Storage model
- New `execution_records` table (separate from `jobs` — keeps job list queries fast)
- Output stored as JSON array in a single `output_log` TEXT column: `[{t, stream, line}, ...]`
- SQLite and Postgres compatible (JSON serialised as TEXT, no JSON-specific column type)
- Key fields: id, job_guid (FK), node_id, status, exit_code, started_at, completed_at, output_log, truncated (bool)

### Output size limit
- Truncate at 1MB of raw output_log JSON
- When truncated: store a `truncated: true` flag on the execution record
- Dashboard shows a visible "Output truncated at 1MB" notice at the end of the log stream

### Security failures
- Signing verification failure, revoked cert, missing verification key → new status `SECURITY_REJECTED`
- Distinct from `FAILED` (runtime error) — makes security events filterable in history
- Error detail stored as an `[ERR]` line in `output_log` alongside the status
- These are pre-execution failures: `started_at` is set, `exit_code` is null

### Claude's Discretion
- Exact colour values and label styling in the log viewer
- Auto-scroll behaviour (scroll to bottom on open, or top)
- Timestamp display format in the log viewer (relative vs absolute)
- Whether to add a "copy to clipboard" / "download" button on the log viewer

</decisions>

<specifics>
## Specific Ideas

- Output viewer should feel like a real terminal log, not a JSON inspector — the current raw JSON display is explicitly what we're replacing
- `SECURITY_REJECTED` status makes the security model observable — if something was rejected, it shows up in history, not just in the audit log

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `JobDetailPanel` in `Jobs.tsx`: existing right-side panel — the new full-screen modal can share the job metadata header pattern
- `authenticatedFetch` in `auth.ts`: all new API calls go through this
- `useWebSocket.ts`: live updates hook — may be useful for streaming future enhancement
- Status badge pattern (`getStatusVariant`): needs extension for `SECURITY_REJECTED` status

### Established Patterns
- Result reporting: node calls `POST /work/{guid}/result` with `{success, result}` — `ResultReport` model needs dedicated `stdout_lines`, `stderr_lines` or `output_log` field
- Job status flow: `PENDING → ASSIGNED → COMPLETED | FAILED` — needs `SECURITY_REJECTED` added
- DB models: `Base.metadata.create_all` at startup — new `ExecutionRecord` table will be auto-created on fresh installs; existing installs need `ALTER TABLE` / migration SQL
- JSON stored as TEXT: consistent with how `job.result`, `node.capabilities`, `node.tags` already work

### Integration Points
- `job_service.report_result()`: main entry point — needs to write to `execution_records` instead of (or in addition to) `job.result`
- `node.py` → `runtime.py`: output capture happens here — needs to return `[{t, stream, line}]` list instead of raw stdout/stderr strings
- `main.py`: new route `GET /jobs/{guid}/executions` and `GET /executions/{id}/output` needed
- `Jobs.tsx`: job row needs a "View Output" button; new `ExecutionLogModal` component needed

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-output-capture*
*Context gathered: 2026-03-04*
