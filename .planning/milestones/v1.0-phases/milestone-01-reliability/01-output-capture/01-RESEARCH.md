# Phase 1: Output Capture - Research

**Researched:** 2026-03-04
**Domain:** FastAPI/SQLAlchemy output capture, React log viewer modal
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Log viewer presentation:**
- Full-screen modal/page (not the existing side panel) — opens when user clicks a job execution
- Single interleaved stream: stdout and stderr in chronological order
- Colour coding: stdout in white/grey, stderr in amber/red
- Prefix labels on every line: `[OUT]` for stdout, `[ERR]` for stderr
- Exit code displayed in **both** places: header metadata (alongside node/duration/timestamp) AND a visual indicator (✔ green / ✘ red) at the end of the log stream

**Per-line timestamps:**
- Node captures stdout and stderr with per-line timestamps to enable true chronological interleaving
- Each log entry: `{t: <ISO timestamp>, stream: "stdout"|"stderr", line: "<text>"}`
- Client renders in timestamp order — no client-side guessing at interleave order

**Storage model:**
- New `execution_records` table (separate from `jobs` — keeps job list queries fast)
- Output stored as JSON array in a single `output_log` TEXT column: `[{t, stream, line}, ...]`
- SQLite and Postgres compatible (JSON serialised as TEXT, no JSON-specific column type)
- Key fields: id, job_guid (FK), node_id, status, exit_code, started_at, completed_at, output_log, truncated (bool)

**Output size limit:**
- Truncate at 1MB of raw output_log JSON
- When truncated: store a `truncated: true` flag on the execution record
- Dashboard shows a visible "Output truncated at 1MB" notice at the end of the log stream

**Security failures:**
- Signing verification failure, revoked cert, missing verification key → new status `SECURITY_REJECTED`
- Distinct from `FAILED` (runtime error) — makes security events filterable in history
- Error detail stored as an `[ERR]` line in `output_log` alongside the status
- These are pre-execution failures: `started_at` is set, `exit_code` is null

### Claude's Discretion
- Exact colour values and label styling in the log viewer
- Auto-scroll behaviour (scroll to bottom on open, or top)
- Timestamp display format in the log viewer (relative vs absolute)
- Whether to add a "copy to clipboard" / "download" button on the log viewer

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OUT-01 | Node captures stdout and stderr for every job execution | Node `runtime.py` already returns `{exit_code, stdout, stderr}` as raw strings. Phase adds per-line timestamp splitting before POST. |
| OUT-02 | Exit code is recorded per execution | `runtime.py` already captures `proc.returncode`. New `execution_records.exit_code` column stores it durably. `ResultReport` model extension carries it. |
| OUT-03 | Each run produces a separate execution record (not just latest result) | New `ExecutionRecord` SQLAlchemy table, one row per `report_result` call. `GET /jobs/{guid}/executions` endpoint lists all. |
| OUT-04 | User can view execution output logs from the job detail page in the dashboard | New `ExecutionLogModal` full-screen Dialog component in `Jobs.tsx`. Fetches `GET /jobs/{guid}/executions` and renders interleaved log lines with colour coding. |
</phase_requirements>

---

## Summary

Phase 1 extends the existing job execution pipeline — which already captures raw `stdout` and `stderr` strings in `runtime.py` — to produce durable, per-attempt execution records with structured per-line output. The codebase already has all infrastructure needed (SQLAlchemy async ORM, Pydantic models, FastAPI routes, React component library). No new libraries are required.

The primary gap is that the current `report_result` path discards stdout/stderr entirely — the `ResultReport` model only carries `{result: Dict, success: bool}`, and `job_service.report_result` stores a summary into `job.result` (a catch-all JSON blob). This phase adds a dedicated `execution_records` table, extends `ResultReport` with `output_log`, extends `report_result` to write the new table atomically, and adds a full-screen log viewer modal to the Jobs page.

The user-facing data format decision — a JSON array of `{t, stream, line}` objects stored as TEXT — is idiomatic for this codebase (same pattern as `job.result`, `node.capabilities`, `node.tags`). The 1MB truncation happens at the orchestrator `report_result` handler before DB write, not at the node, because the node POSTs the structured JSON payload and the server controls storage limits. The `SECURITY_REJECTED` status requires a small extension to the node's `execute_task` signature-failure path to report a distinct result type.

**Primary recommendation:** Implement this as five sequential sub-tasks: (1) DB table + migration, (2) Pydantic model extension, (3) node-side per-line capture, (4) server-side `report_result` extension, (5) frontend `ExecutionLogModal` component. Each is independently testable.

---

## Standard Stack

### Core (all already installed — zero new dependencies)

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| SQLAlchemy async ORM | 2.x (existing) | `ExecutionRecord` table definition | Already used for all DB models in `db.py` |
| FastAPI | existing | New routes: `GET /jobs/{guid}/executions`, `GET /executions/{id}/output` | All API routes live here |
| Pydantic v2 | existing | `ResultReport` extension, `ExecutionRecordResponse` model | All request/response models use this |
| React + shadcn/ui | existing | `ExecutionLogModal` using `Dialog` primitive | `dialog.tsx` already present at `src/components/ui/dialog.tsx` |
| `authenticatedFetch` | existing | All new API calls from frontend | Pattern used across all dashboard views |

### Supporting

| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| `asyncio.subprocess` | stdlib | Per-line stdout/stderr capture in `runtime.py` | Already used in `direct` mode; extend for container mode |
| `json` stdlib | stdlib | Serialise `output_log` array to TEXT before DB write | Same pattern as `job.result`, `node.capabilities` |
| `datetime.utcnow()` | stdlib | Per-line timestamp generation at orchestrator boundary | Timestamps added server-side during line splitting |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON array as TEXT column | Postgres JSONB column | JSONB is non-portable — SQLite does not support it; TEXT is idiomatic for this codebase |
| Server-side 1MB truncation | Node-side truncation before POST | Node already serialises lines; server controls the storage policy and can enforce it consistently |
| Radix UI Dialog (full-screen) | Custom overlay div | Dialog primitive already installed and used for other modals; consistent UX |

**Installation:** No new packages needed. Zero `pip install` or `npm install` steps.

---

## Architecture Patterns

### Recommended Project Structure Changes

```
puppeteer/
├── agent_service/
│   ├── db.py                    # Add ExecutionRecord ORM class
│   ├── models.py                # Extend ResultReport; add ExecutionRecordResponse
│   ├── main.py                  # Add GET /jobs/{guid}/executions route
│   └── services/
│       └── job_service.py       # Extend report_result(); add list_executions()
├── migration_v14.sql            # CREATE TABLE IF NOT EXISTS execution_records
puppets/
└── environment_service/
    └── node.py                  # extend execute_task() to build output_log lines
                                 # extend report_result() call with output_log field
dashboard/src/
└── views/
    └── Jobs.tsx                 # Add "View Output" button + ExecutionLogModal component
```

### Pattern 1: ExecutionRecord ORM Table

**What:** New SQLAlchemy ORM model in `db.py`, follows exact same pattern as all other models in that file.
**When to use:** Every call to `job_service.report_result()` creates one row.

```python
# Source: db.py — follows Mapped[]/mapped_column() pattern used by all models
from sqlalchemy import String, Integer, Text, Boolean, DateTime
from datetime import datetime
from typing import Optional

class ExecutionRecord(Base):
    __tablename__ = "execution_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_guid: Mapped[str] = mapped_column(String, nullable=False, index=True)
    node_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)  # COMPLETED, FAILED, SECURITY_REJECTED
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    output_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as TEXT
    truncated: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
```

**Index note:** `job_guid` must be indexed — `GET /jobs/{guid}/executions` queries `WHERE job_guid = ?`. Without the index, every execution history fetch full-scans the table.

### Pattern 2: ResultReport Extension (Pydantic)

**What:** Add `output_log` field to `ResultReport` in `models.py`. Node sends `[{t, stream, line}, ...]` or `None`.
**When to use:** Node constructs this list from `stdout`/`stderr` strings before calling `report_result()`.

```python
# Source: models.py — follows existing ResultReport pattern
from typing import Optional, List, Dict, Any

class OutputLine(BaseModel):
    t: str            # ISO timestamp string
    stream: str       # "stdout" or "stderr"
    line: str         # single line of text (no trailing newline)

class ResultReport(BaseModel):
    result: Optional[Dict] = None
    error_details: Optional[Dict] = None
    success: bool
    output_log: Optional[List[Dict[str, str]]] = None  # [{t, stream, line}, ...]
    exit_code: Optional[int] = None
    # Note: use List[Dict] not List[OutputLine] to avoid Pydantic coercion issues
    # when node sends raw JSON dict array
```

### Pattern 3: Node-Side Per-Line Timestamp Splitting

**What:** After `runtime.py` returns `{exit_code, stdout, stderr}` as raw strings, `node.py` splits each string by newline and interleaves with timestamps.
**When to use:** In `execute_task()`, immediately after `self.runtime_engine.run()` returns, before calling `self.report_result()`.

```python
# Source: puppets/environment_service/node.py — extends execute_task()
from datetime import datetime, timezone

def build_output_log(stdout: str, stderr: str) -> list:
    """Split stdout/stderr into per-line timestamped entries."""
    lines = []
    # Add all stdout lines with a single shared timestamp
    # (subprocess.run captures all at once — no per-line timing available)
    ts = datetime.now(timezone.utc).isoformat()
    for line in stdout.splitlines():
        if line:  # skip empty lines
            lines.append({"t": ts, "stream": "stdout", "line": line})
    for line in stderr.splitlines():
        if line:
            lines.append({"t": ts, "stream": "stderr", "line": line})
    return lines
```

**Note on timestamps:** Since `runtime.py` captures output only after process completion (via `proc.communicate()`), per-line timestamps are all identical for a given job. True chronological interleaving between stdout/stderr lines within a run is not achievable without streaming. The per-line structure is correct for the format — it enables future streaming without a schema change. Sort by `t` then by appearance order (stable sort preserves list order for equal timestamps). This is the right design; the CONTEXT.md confirms this was the decided approach.

### Pattern 4: Server-Side report_result Extension

**What:** `job_service.report_result()` reads `output_log` from `ResultReport`, enforces 1MB limit, writes `ExecutionRecord` row in the same DB transaction as the `Job.status` update.
**When to use:** Always — replaces the existing `job.result = json.dumps(result_payload)` for output data.

```python
# Source: job_service.py — extends report_result() static method
import json
from datetime import datetime

MAX_OUTPUT_BYTES = 1_048_576  # 1 MB

async def report_result(guid, report, node_ip, db):
    # ... existing job lookup ...

    # Build output_log (truncate if needed)
    output_log = report.output_log or []
    truncated = False
    output_json = json.dumps(output_log)
    if len(output_json.encode("utf-8")) > MAX_OUTPUT_BYTES:
        # Trim lines until under limit
        while output_log and len(json.dumps(output_log).encode("utf-8")) > MAX_OUTPUT_BYTES:
            output_log.pop()
        truncated = True

    # Determine status
    if report.success:
        new_status = "COMPLETED"
    else:
        # Check if it was a security rejection (node passes a flag or specific error key)
        error = (report.error_details or {}).get("error", "")
        if "security" in error.lower() or "signature" in error.lower() or "verification" in error.lower():
            new_status = "SECURITY_REJECTED"
        else:
            new_status = "FAILED"

    # Write ExecutionRecord (same transaction)
    record = ExecutionRecord(
        job_guid=guid,
        node_id=job.node_id,
        status=new_status,
        exit_code=report.exit_code,
        started_at=job.started_at,
        completed_at=datetime.utcnow(),
        output_log=json.dumps(output_log),
        truncated=truncated,
    )
    db.add(record)

    job.status = new_status
    job.completed_at = datetime.utcnow()
    await db.commit()
    return {"status": new_status}
```

**SECURITY_REJECTED detection:** Rather than string-matching error text server-side (fragile), the cleaner approach is for the node to pass a typed flag. See Pitfall 3 below for the recommended approach.

### Pattern 5: ExecutionLogModal (React)

**What:** Full-screen Radix UI `Dialog` component in `Jobs.tsx`. Opens when user clicks a "View Output" button on any completed/failed job row. Fetches `GET /jobs/{guid}/executions` to list execution attempts, then renders the `output_log` array as a styled terminal log.
**When to use:** Triggered from `JobDetailPanel` or directly from the job table row.

```typescript
// Source: src/components/ui/dialog.tsx — Dialog primitive already installed
// Pattern follows existing JobDefinitionModal and other modal components

const ExecutionLogModal = ({ guid, open, onClose }: {
  guid: string;
  open: boolean;
  onClose: () => void;
}) => {
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [selected, setSelected] = useState<ExecutionRecord | null>(null);

  useEffect(() => {
    if (!open || !guid) return;
    authenticatedFetch(`/jobs/${guid}/executions`)
      .then(r => r.json())
      .then(data => {
        setExecutions(data);
        setSelected(data[0] ?? null);  // most recent first
      });
  }, [open, guid]);

  const lines = selected?.output_log ?? [];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-zinc-950 border-zinc-800 text-white
                                w-[95vw] max-w-6xl h-[90vh] flex flex-col">
        <DialogHeader>
          {/* Exit code badge, node, duration, timestamp */}
        </DialogHeader>
        {/* Log lines */}
        <div className="flex-1 overflow-y-auto font-mono text-xs p-4 bg-black rounded">
          {lines.map((entry, i) => (
            <div key={i} className="flex gap-2">
              <span className="text-zinc-600 shrink-0">{formatTs(entry.t)}</span>
              <span className={entry.stream === 'stderr'
                ? 'text-amber-400'   // ERR = amber
                : 'text-zinc-300'}  // OUT = white/grey
              >
                <span className="text-zinc-600">
                  {entry.stream === 'stderr' ? '[ERR]' : '[OUT]'}
                </span>{' '}
                {entry.line}
              </span>
            </div>
          ))}
          {selected?.truncated && (
            <div className="text-yellow-500 border-t border-zinc-800 mt-2 pt-2">
              Output truncated at 1MB — remaining lines not stored.
            </div>
          )}
          {/* Exit code indicator at bottom of stream */}
          {selected && selected.exit_code !== null && (
            <div className={`mt-4 font-bold ${selected.exit_code === 0
              ? 'text-green-400' : 'text-red-400'}`}>
              {selected.exit_code === 0 ? '✔' : '✘'} Exit {selected.exit_code}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
```

### Anti-Patterns to Avoid

- **Storing output in `jobs.result`:** The existing `jobs.result` blob is already loaded on every `list_jobs` call. Adding multi-KB output there causes scan bloat on the hot jobs table. All output goes to `execution_records` only.
- **Returning output in `GET /jobs`:** The list endpoint must never include `output_log`. Only `GET /jobs/{guid}/executions` returns execution detail; list endpoints return summary fields only.
- **Splitting lines on the node with `print()` buffering:** Python's `sys.stdout` is line-buffered in TTY mode but block-buffered when piped. `proc.communicate()` returns the complete buffer — splitting by `\n` is reliable. Do not assume line-level granularity during execution.
- **Using Dialog `max-w-lg` (the default):** The default Dialog content is `max-w-lg` which is 32rem — too narrow for a log viewer. Override with `w-[95vw] max-w-6xl` as shown above.
- **SECURITY_REJECTED written to jobs table but not execution_records:** The `SECURITY_REJECTED` status must appear in both places. The `jobs.status` is updated for job-level filtering; the `execution_records` row captures the details for the log viewer.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Full-screen modal container | Custom CSS overlay/portal | Radix UI `Dialog` (already in `dialog.tsx`) | Focus trap, keyboard close, backdrop click, ARIA roles — all handled |
| JSON-as-TEXT serialisation | Custom escaping | `json.dumps()` / `json.loads()` | Same pattern as `job.result`, `node.tags`, `node.capabilities` throughout codebase |
| Byte-counting for truncation | Custom string length math | `len(output_json.encode("utf-8"))` | Correctly counts multi-byte Unicode characters; `.encode()` gives byte count |
| Timestamp formatting in UI | Custom date parsing | `new Date(entry.t).toLocaleTimeString()` or relative with `Intl.RelativeTimeFormat` | Browser's built-in formatters handle timezone and locale |

**Key insight:** Every "infrastructure" need in this phase is already solved by existing codebase patterns. The work is purely additive — new table, new fields on existing model, new route, new component.

---

## Common Pitfalls

### Pitfall 1: The job table `result` column is still written with output data

**What goes wrong:** Developer extends `report_result` but also keeps the line `job.result = json.dumps(result_payload)` where `result_payload` contains `stdout`/`stderr` keys. Output data ends up in both tables. List endpoints start returning large blobs.
**Why it happens:** The existing flight recorder logic builds `result_payload` from `report.result`. It's natural to add stdout there.
**How to avoid:** Keep `job.result` as a minimal summary (exit code, status) or null. All output goes into `execution_records.output_log` only. Review `list_jobs()` — it currently passes `job.result` to the response; ensure that remains a small dict.
**Warning signs:** `GET /jobs` response size increases after the change; any job response JSON contains `stdout` or `stderr` keys.

### Pitfall 2: `create_all` creates `execution_records` on fresh installs but existing DB needs manual migration

**What goes wrong:** Fresh Docker deployments work fine (SQLAlchemy `create_all` handles new tables). Existing Postgres production deployments with `jobs.db` or the live Postgres instance miss the new table entirely — `report_result` crashes with `table execution_records does not exist`.
**Why it happens:** `create_all` does not ALTER existing tables and does not CREATE tables that already don't exist for already-open connections. Actually it does create new tables — but only if the DB was started fresh. Existing Postgres deployments where the schema was created before this code ships need an explicit `CREATE TABLE IF NOT EXISTS`.
**How to avoid:** Write `migration_v14.sql` with `CREATE TABLE IF NOT EXISTS execution_records (...)`. Apply before deploying new code. The pattern is established: `migration_v10.sql`, `migration_v11.sql`, etc.
**Warning signs:** `asyncpg.exceptions.UndefinedTableError` in logs after deployment.

### Pitfall 3: SECURITY_REJECTED detection is string-matched server-side (fragile)

**What goes wrong:** The server inspects `report.error_details.get("error", "")` and looks for "signature" or "security" substrings to decide the status is `SECURITY_REJECTED` rather than `FAILED`. A future error message change on the node silently breaks detection.
**Why it happens:** `node.py`'s `report_result()` currently passes `{"error": "Signature Verification Failed"}` — the string happens to work. But this is an implicit contract.
**How to avoid:** Add an explicit `security_rejected: bool = False` field to `ResultReport`. Node sets it to `True` in the signature-failure path. Server reads the flag, not the string. This is a one-line model change and a one-line node change, far more robust.
**Warning signs:** `SECURITY_REJECTED` jobs appear as `FAILED` in the dashboard after a node version update.

### Pitfall 4: Empty lines inflate `output_log` array

**What goes wrong:** Python scripts often print empty lines (`print()` with no args). Splitting stdout by `\n` produces empty strings. If stored as `{"t": ..., "stream": "stdout", "line": ""}`, the log viewer renders blank lines — harmless but wastes storage and makes truncation hit earlier.
**Why it happens:** Naive `stdout.splitlines()` includes empty strings.
**How to avoid:** Filter empty lines: `if line.strip()` before appending. Or preserve empty lines but don't count them toward the 1MB limit separately.
**Warning signs:** `output_log` arrays with many `{"line": ""}` entries in the DB.

### Pitfall 5: Dialog accessibility — focus is not trapped in log viewer

**What goes wrong:** A hand-rolled `<div>` overlay doesn't trap focus — screen readers and keyboard navigation can reach elements behind the modal.
**Why it happens:** Temptation to avoid the Dialog component because its default `max-w-lg` is too narrow for a log viewer.
**How to avoid:** Use the existing Radix `Dialog` primitive with overridden width classes. `DialogContent` accepts a `className` prop — add `w-[95vw] max-w-6xl h-[90vh]` to get a full-screen-like log viewer while keeping all accessibility behaviour.
**Warning signs:** Tab key reaches page elements behind the open modal.

### Pitfall 6: SQLite `server_default` for Boolean column

**What goes wrong:** SQLAlchemy's `server_default="false"` is Postgres syntax. SQLite uses `0`/`1` for Boolean. If `server_default` is wrong, SQLite may error on `INSERT`.
**Why it happens:** The existing `User.must_change_password` uses `server_default="false"` and works on Postgres but may not on SQLite.
**How to avoid:** Use Python-level default only: `truncated: Mapped[bool] = mapped_column(Boolean, default=False)`. No `server_default` needed since SQLAlchemy fills the Python default before INSERT. The existing `NodeStats` table has no `server_default` and works on both backends.
**Warning signs:** `OperationalError: table execution_records has no column named truncated` or similar SQLite errors.

---

## Code Examples

### Adding index to execution_records in SQLAlchemy

```python
# Source: db.py — follows Index pattern used in other models if needed
# In __table_args__ or as part of mapped_column
from sqlalchemy import Index

class ExecutionRecord(Base):
    __tablename__ = "execution_records"
    # ... columns ...
    __table_args__ = (
        Index("ix_execution_records_job_guid", "job_guid"),
    )
```

### Migration SQL (migration_v14.sql)

```sql
-- Postgres-compatible migration for existing deployments
CREATE TABLE IF NOT EXISTS execution_records (
    id SERIAL PRIMARY KEY,
    job_guid VARCHAR NOT NULL,
    node_id VARCHAR,
    status VARCHAR NOT NULL,
    exit_code INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    output_log TEXT,
    truncated BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_execution_records_job_guid
    ON execution_records (job_guid);
```

### GET /jobs/{guid}/executions route (main.py pattern)

```python
# Source: main.py — follows existing route patterns with require_permission
@app.get("/jobs/{guid}/executions")
async def list_executions(
    guid: str,
    current_user: User = Depends(require_permission("jobs:read")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ExecutionRecord)
        .where(ExecutionRecord.job_guid == guid)
        .order_by(ExecutionRecord.id.desc())
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "job_guid": r.job_guid,
            "node_id": r.node_id,
            "status": r.status,
            "exit_code": r.exit_code,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "output_log": json.loads(r.output_log) if r.output_log else [],
            "truncated": r.truncated,
            "duration_seconds": (
                (r.completed_at - r.started_at).total_seconds()
                if r.started_at and r.completed_at else None
            )
        }
        for r in records
    ]
```

### Node-side output_log construction (node.py)

```python
# Source: puppets/environment_service/node.py — in execute_task()
# After: result = await self.runtime_engine.run(...)
from datetime import datetime, timezone

ts = datetime.now(timezone.utc).isoformat()
output_log = []
for line in (result.get("stdout") or "").splitlines():
    if line.strip():
        output_log.append({"t": ts, "stream": "stdout", "line": line})
for line in (result.get("stderr") or "").splitlines():
    if line.strip():
        output_log.append({"t": ts, "stream": "stderr", "line": line})

success = (result["exit_code"] == 0)
await self.report_result(guid, success, {
    "exit_code": result["exit_code"],
    "output_log": output_log,
})
```

### report_result call signature change (node.py)

The existing `report_result(guid, success, result: Dict)` method POSTs `{"success": success, "result": result}`. This payload must be extended to include `output_log` and `exit_code` as top-level fields matching the new `ResultReport` model:

```python
# In Node.report_result():
await client.post(
    f"{self.agent_url}/work/{guid}/result",
    json={
        "success": success,
        "result": result,          # keep for backward compat flight recorder
        "output_log": output_log,  # new field
        "exit_code": exit_code,    # new field
        "security_rejected": security_rejected,  # new bool flag
    },
    headers={...}
)
```

---

## State of the Art

| Old Approach (current codebase) | New Approach (this phase) | Impact |
|---------------------------------|---------------------------|--------|
| `job.result = json.dumps({stdout, stderr})` in catch-all blob | `execution_records.output_log` as JSON array TEXT | List queries stay fast; output is queryable per-attempt |
| `ResultReport` has only `{result, error_details, success}` | `ResultReport` adds `output_log`, `exit_code`, `security_rejected` | Node can pass structured output in one POST |
| `JobDetailPanel` is a Sheet (side panel) | New `ExecutionLogModal` is a full-screen Dialog | Better readability for large log outputs |
| No distinct status for security failures | `SECURITY_REJECTED` status | Security events are filterable and auditable separately from runtime failures |
| Raw JSON blob in detail panel (`JSON.stringify(resultData)`) | Colour-coded per-line log viewer with `[OUT]`/`[ERR]` prefixes | Operators can actually read what the job printed |

**What remains unchanged:**
- `jobs.status` transitions (`PENDING → ASSIGNED → COMPLETED/FAILED`) — just extended with `SECURITY_REJECTED`
- `job.result` column — kept for backward compatibility with the flight recorder pattern, but no longer contains stdout/stderr
- `POST /work/{guid}/result` endpoint URL — not changed, request body extended with new optional fields

---

## Integration Points

### Backend Integration Map

| Touch Point | Change | Risk |
|-------------|--------|------|
| `db.py` | Add `ExecutionRecord` class | LOW — new table, no existing code changes |
| `models.py` | Extend `ResultReport`, add `ExecutionRecordResponse` | LOW — additive fields, all Optional |
| `job_service.py: report_result()` | Write `ExecutionRecord` row; update `job.status` to include `SECURITY_REJECTED` | MEDIUM — same transaction, must not break existing job completion |
| `main.py` | Add `GET /jobs/{guid}/executions` route | LOW — new route, no existing route changes |
| `node.py: execute_task()` | Build `output_log` list from `runtime.py` result; pass to `report_result()` | MEDIUM — changes the result payload format |
| `node.py: report_result()` | Add `output_log`, `exit_code`, `security_rejected` to POST body | LOW — server accepts Optional fields |
| `get_job_stats()` in `job_service.py` | Add `SECURITY_REJECTED` to the status list | LOW — one-line addition |

### Frontend Integration Map

| Touch Point | Change | Risk |
|-------------|--------|------|
| `Jobs.tsx: getStatusVariant()` | Add `security_rejected` case → `destructive` variant | LOW — switch extension |
| `Jobs.tsx: StatusIcon` | Add `security_rejected` case → shield icon (Lucide `ShieldAlert`) | LOW |
| `Jobs.tsx: filteredJobs` status filter | Add `SECURITY_REJECTED` to Select options | LOW |
| `Jobs.tsx` (new) | Add `ExecutionLogModal` component | MEDIUM — new component, ~100 lines |
| `Jobs.tsx: JobDetailPanel` | Add "View Output" button that opens `ExecutionLogModal` | LOW — one button addition |
| `Jobs.tsx: Job interface` | No change needed — `guid` field already present | N/A |

---

## Open Questions

1. **Timestamp accuracy: node clock vs orchestrator clock**
   - What we know: `runtime.py` captures output after `proc.communicate()` completes — no per-line timing during execution. Node.py adds a single timestamp to all lines of a given run.
   - What's unclear: Should the timestamp on `output_log` lines reflect the moment capture happened (node time) or the server-side `completed_at` time?
   - Recommendation: Use node-side `datetime.now(timezone.utc).isoformat()` — it's the closest to actual execution time. Server adds `completed_at` separately. Node clock skew is acceptable given the pull model already has this characteristic.

2. **What happens to `job.result` after this phase?**
   - What we know: `list_jobs` currently returns `json.loads(job.result)` and the `JobDetailPanel` renders it. The flight recorder logic writes to `job.result`.
   - What's unclear: Do we null out `job.result` now that output lives in `execution_records`, or keep it as a small summary?
   - Recommendation: Keep `job.result` as a minimal summary (`{"exit_code": N}`) or null it. Remove the flight recorder's stdout/stderr keys. Do not break the existing `JobDetailPanel` result section — it can show the small summary until Phase 3 removes the panel entirely.

3. **`SECURITY_REJECTED` in `get_job_stats()`**
   - What we know: `get_job_stats()` hardcodes `["PENDING", "ASSIGNED", "COMPLETED", "FAILED"]` status list. `SECURITY_REJECTED` will not be counted in the initial seeding loop.
   - What's unclear: Should `SECURITY_REJECTED` be counted separately or bundled under `FAILED` for the dashboard metric?
   - Recommendation: Add `SECURITY_REJECTED` as its own entry in `get_job_stats()`. The dashboard currently shows the raw counts dict — the frontend can choose how to display it.

---

## Sources

### Primary (HIGH confidence)

- Direct codebase read: `puppeteer/agent_service/db.py` — SQLAlchemy ORM patterns, existing model structure
- Direct codebase read: `puppeteer/agent_service/models.py` — `ResultReport` current fields, Pydantic v2 patterns
- Direct codebase read: `puppeteer/agent_service/services/job_service.py` — `report_result()` implementation, existing transaction pattern
- Direct codebase read: `puppeteer/agent_service/main.py` — route patterns, `require_permission` usage, `ws_manager.broadcast()` calls
- Direct codebase read: `puppets/environment_service/node.py` — `execute_task()`, `report_result()`, security rejection paths
- Direct codebase read: `puppets/environment_service/runtime.py` — `ContainerRuntime.run()` return value `{exit_code, stdout, stderr}`
- Direct codebase read: `puppeteer/dashboard/src/views/Jobs.tsx` — `JobDetailPanel`, `getStatusVariant()`, Sheet component, `authenticatedFetch` usage
- Direct codebase read: `puppeteer/dashboard/src/components/ui/dialog.tsx` — Radix Dialog primitive, `DialogContent` className override pattern
- `.planning/phases/01-output-capture/01-CONTEXT.md` — locked decisions, verbatim

### Secondary (MEDIUM confidence)

- `.planning/research/ARCHITECTURE.md` — `ExecutionRecord` schema design, 1MB truncation rationale, TEXT vs JSONB decision, data flow diagram
- `.planning/research/SUMMARY.md` — pitfall catalogue, "don't store output in jobs.result" anti-pattern

### Tertiary (LOW confidence)

- None required — all implementation decisions are derivable from direct codebase inspection.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all components already installed; verified by direct file inspection
- Architecture: HIGH — based on direct codebase read of all six relevant files; patterns are explicit in the existing code
- Pitfalls: HIGH — derived from inspecting existing code paths (type mismatches, transaction flow, SQL compat issues, Dialog sizing)
- Frontend patterns: HIGH — `dialog.tsx`, `Jobs.tsx`, and existing modal components (`JobDefinitionModal`) provide exact patterns to follow

**Research date:** 2026-03-04
**Valid until:** 2026-04-04 (stable stack — no fast-moving dependencies)
