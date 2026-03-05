# Phase 2: Retry Policy - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Failed jobs retry automatically with configurable backoff, dead-letter after exhausting all retries, and crashed-node zombie jobs are reaped inline during work polling and rescheduled — no failed job is silently lost. Cron-scheduled jobs skip a new instance if the previous execution is still active (no pile-up). Operators can manually re-queue dead-letter and failed jobs from the dashboard.

Execution history view (queryable timeline) is Phase 3. Notifications on dead-letter are Phase 2 backlog / v2.

</domain>

<decisions>
## Implementation Decisions

### Retry scope
- `max_retries` lives on **both** `ScheduledJob` definitions AND individual `Job` rows — all jobs carry a retry policy regardless of origin
- Retries use the **same GUID**: the original Job row is reset to PENDING with `retry_count` incremented; each attempt writes its own `ExecutionRecord`
- New columns on `Job`: `max_retries` (int, default 0), `retry_count` (int, default 0), `retry_after` (DateTime nullable — when job becomes eligible again), `backoff_multiplier` (float, default 2.0), `timeout_minutes` (int nullable)
- New columns on `ScheduledJob`: `max_retries` (int, default 0), `backoff_multiplier` (float, default 2.0), `timeout_minutes` (int nullable) — inherited by Job at creation time
- When all retries exhausted → job moves to **`DEAD_LETTER`** terminal status (distinct from `FAILED`)

### Failure classification
- **Node explicitly flags retriability** in `ResultReport`: add `retriable: Optional[bool]` field
- **Default (field absent)** → **non-retriable** — existing nodes that don't send the flag will not retry; redeploy nodes after upgrading server to get full benefit
- `SECURITY_REJECTED` → always non-retriable (Phase 1 decision, unchanged)
- **Manual cancellation** by operator → always terminal; no retries regardless of `max_retries`
- **Cron overlap prevention**: when a cron fires, check if the most recent Job from that `ScheduledJob` definition is still PENDING, ASSIGNED, or RETRYING — if so, skip the new instance and log the skip as an audit event

### Zombie timeout
- **Global Config table default** (`zombie_timeout_minutes`, sensible default: 30 min) + **per-job override** via `Job.timeout_minutes` column (null = use global)
- Zombie detection runs **inline at `pull_work()`**: before selecting a new job, scan for ASSIGNED jobs on the polling node that have exceeded their timeout
- Zombie reclaim **counts as a retry attempt**: `retry_count` incremented; if retries exhausted → DEAD_LETTER; if retries remain → reset to PENDING with backoff applied
- Zombie reclaim writes an ExecutionRecord with status `ZOMBIE_REAPED` and no output log (node never reported)

### Dashboard retry UX
- Jobs waiting in backoff show status **`RETRYING`** — distinct from `PENDING` (first attempt) and `FAILED` (terminal failure that can still be manually retried)
- **Attempt column** in the job table: shows `2/3` for the current attempt out of max. Blank for jobs with `max_retries = 0`
- **Job detail panel** shows: `retry_after` countdown ("Next attempt in 4m 30s"), full attempt history linked to ExecutionRecords
- **`DEAD_LETTER`** gets its own filter chip in the status bar (dark red / maroon) — separate from FAILED
- **Retry button** on DEAD_LETTER and FAILED jobs: operator can manually re-queue (resets `retry_count` to 0, clears `retry_after`, sets status to PENDING). Requires `jobs:write` permission.

### Claude's Discretion
- Exact backoff formula (base formula: `backoff_multiplier ^ retry_count` seconds, with jitter ±20%)
- Initial backoff delay for retry_count = 1 (suggest: 30s)
- Cap on maximum backoff interval (suggest: 1 hour)
- Exact color values for RETRYING and DEAD_LETTER status badges
- Whether RETRYING status is included in the server-side status filter (it should be)

</decisions>

<specifics>
## Specific Ideas

- "Once we upgrade the server on this run, we should redeploy the nodes for full compatibility" — non-retriable default is an intentional migration step, not a permanent design choice
- Cron overlap prevention is motivated by: if a job is retrying and the next cron fires, we don't want two concurrent instances of the same scheduled job competing for the same node resources

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `report_result()` in `job_service.py`: main entry point where retry logic triggers — check `retriable` flag, increment `retry_count`, compute `retry_after`, set status RETRYING or DEAD_LETTER
- `pull_work()` in `job_service.py`: zombie reaper runs here — scan ASSIGNED jobs for this node past their timeout before selecting new work
- `SchedulerService.execute_scheduled_job()` in `scheduler_service.py`: cron overlap check goes here — query most recent Job for this `scheduled_job_id`, skip if active
- `get_job_stats()` in `job_service.py`: needs RETRYING and DEAD_LETTER added to the standard status set
- `ResultReport` Pydantic model in `models.py`: needs `retriable: Optional[bool] = None` field
- `getStatusVariant()` pattern in `Jobs.tsx`: needs RETRYING (amber/yellow) and DEAD_LETTER (dark red) variants

### Established Patterns
- Status flow already extensible: `PENDING → ASSIGNED → COMPLETED | FAILED | SECURITY_REJECTED` — add `RETRYING` and `DEAD_LETTER` without breaking existing checks
- JSON-as-TEXT for complex fields: retry config columns are simple scalars (int/float/datetime), not JSON — first-class columns appropriate here
- Config table (`key`/`value` TEXT): existing pattern for `zombie_timeout_minutes` global setting
- DB migration pattern: `create_all` handles new tables; existing `jobs` and `scheduled_jobs` tables need `ALTER TABLE` migration SQL (migration_v15.sql)
- `authenticatedFetch` in `auth.ts`: Retry button calls `POST /jobs/{guid}/retry` (new endpoint)
- Status filter chips already exist in `Jobs.tsx` — add RETRYING and DEAD_LETTER chips following the existing pattern

### Integration Points
- `pull_work()`: zombie scan runs before job selection loop; reclaimed zombie jobs are immediately available for re-assignment in the same poll response
- `execute_scheduled_job()`: overlap check queries `Job` table by `scheduled_job_id` for active statuses
- New endpoint: `POST /jobs/{guid}/retry` — manual re-queue; requires `jobs:write`
- `WorkResponse` / `JobCreate` models: propagate `max_retries`, `backoff_multiplier`, `timeout_minutes` from ScheduledJob at spawn time

</code_context>

<deferred>
## Deferred Ideas

- Notifications when a job hits DEAD_LETTER — Phase 2 backlog / v2 (NOTF-01 requirement)
- Per-exit-code retry classification as an alternative to the `retriable` flag — noted but not needed given node-side flagging

</deferred>

---

*Phase: 02-retry-policy*
*Context gathered: 2026-03-05*
