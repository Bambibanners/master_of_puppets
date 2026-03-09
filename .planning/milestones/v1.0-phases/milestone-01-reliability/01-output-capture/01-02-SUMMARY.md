---
phase: 01-output-capture
plan: "02"
subsystem: pipeline
tags: [python, fastapi, sqlalchemy, node-agent, execution-records, output-capture]

# Dependency graph
requires:
  - phase: 01-01
    provides: ExecutionRecord ORM model in db.py; extended ResultReport Pydantic model
provides:
  - build_output_log() helper in node.py: [{t, stream, line}] per-line log entries from stdout/stderr
  - Extended report_result() in node.py: POSTs output_log, exit_code, security_rejected fields
  - security_rejected=True on all three security-rejection paths in execute_task()
  - ExecutionRecord write in job_service.report_result() for every result (COMPLETED/FAILED/SECURITY_REJECTED)
  - 1MB output truncation with truncated=True flag on ExecutionRecord
  - Minimal job.result: no stdout/stderr in jobs table — output_log lives in execution_records only
  - SECURITY_REJECTED counted in get_job_stats()
affects:
  - 01-03 (GET /executions/{guid} route reads execution_records rows written here)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "build_output_log() is module-level (not a method) — importable for unit testing without Node instantiation"
    - "report_result() uses keyword-only defaults (output_log=None, exit_code=None, security_rejected=False) — backward compat for sidecar callers"
    - "1MB truncation pops from the tail of output_log (most recent lines discarded) to stay under limit"
    - "ExecutionRecord and job status updated in the same transaction (one db.commit()) — no partial writes"
    - "SECURITY_REJECTED excluded from success_rate denominator in get_job_stats() — security events tracked separately from operational failures"

key-files:
  created:
    - puppets/environment_service/tests/test_output_log.py
    - puppeteer/tests/test_execution_record.py
  modified:
    - puppets/environment_service/node.py
    - puppeteer/agent_service/services/job_service.py

key-decisions:
  - "build_output_log filters whitespace-only lines (line.strip() check) to avoid storing blank entries in execution_records"
  - "job.result stores only minimal summary (exit_code or flight_recorder) — stdout/stderr exclusively in execution_records.output_log"
  - "SECURITY_REJECTED status written to both job.status AND ExecutionRecord.status for queryability"
  - "Truncation pops from tail (most recent output) rather than head — preserves startup lines which are more diagnostic"

patterns-established:
  - "TDD pattern: RED test commit → GREEN implementation commit — clear audit trail of intent before code"
  - "AsyncMock/MagicMock distinction: db.add() is sync (MagicMock), db.execute() is async (AsyncMock) — tests must match"

requirements-completed:
  - OUT-01
  - OUT-02
  - OUT-03

# Metrics
duration: 4min
completed: 2026-03-04
---

# Phase 1 Plan 02: Pipeline Extension Summary

**build_output_log() in node.py + ExecutionRecord writes in job_service.py — every job result now persists structured per-line output with 1MB truncation and SECURITY_REJECTED classification**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-04T21:19:15Z
- **Completed:** 2026-03-04T21:24:02Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 4 (node.py, job_service.py, 2 test files)

## Accomplishments
- `build_output_log(stdout, stderr)` module-level function: splits by lines, filters whitespace-only, returns `[{t, stream, line}]` with UTC ISO timestamp
- `report_result()` in node.py extended with `output_log`, `exit_code`, `security_rejected` keyword args (defaults preserve backward compat for sidecar callers)
- All three security-rejection paths in `execute_task()` now set `security_rejected=True`
- Successful runs call `build_output_log()` and forward `output_log` + `exit_code` in the POST
- `job_service.report_result()` writes an `ExecutionRecord` row for every job result in the same transaction as the `job.status` update
- 1MB truncation: pops entries from output_log tail until under limit; `truncated=True` stored on the record
- `job.result` contains only minimal summary: `{exit_code}` on success, `{flight_recorder: ...}` on failure — no stdout/stderr in the jobs table
- `get_job_stats()` includes `SECURITY_REJECTED` in the status list; excluded from `success_rate` denominator

## Task Commits

Each task was committed atomically with TDD RED/GREEN sequence:

1. **Task 1 RED: Failing tests for build_output_log and extended report_result** - `842cc8d` (test)
2. **Task 1 GREEN: Extend node.py — build_output_log and extended report_result** - `47a95cc` (feat)
3. **Task 2 RED: Failing tests for job_service ExecutionRecord write** - `c4fed47` (test)
4. **Task 2 GREEN: Extend job_service.report_result() to write ExecutionRecord** - `ee247eb` (feat)

## Files Created/Modified
- `puppets/environment_service/node.py` - Added `from datetime import datetime, timezone`; `build_output_log()` function; extended `report_result()` signature with 3 kwargs; 3 security-rejection paths set `security_rejected=True`; successful run path calls `build_output_log()` and passes `exit_code`
- `puppeteer/agent_service/services/job_service.py` - Added `ExecutionRecord` to db import; `MAX_OUTPUT_BYTES = 1_048_576`; replaced `report_result()` job-completion logic with status classification, truncation, `ExecutionRecord` write, and minimal `job.result`; added `SECURITY_REJECTED` to `get_job_stats()`
- `puppets/environment_service/tests/test_output_log.py` - 7 tests: build_output_log normal/empty/whitespace/timestamp/keys, report_result extended fields, security_rejected flag
- `puppeteer/tests/test_execution_record.py` - 10 tests: constant, source inspection tests (5), integration-style tests for COMPLETED/SECURITY_REJECTED/FAILED/truncation paths

## Decisions Made
- Truncation pops from tail (most recent lines) not head: startup/import lines are more diagnostic for debugging, so they survive truncation
- `job.result` minimal summary: the plan required no stdout/stderr in `job.result`; implemented as `{"exit_code": N}` for success/security-rejected, `{"flight_recorder": {...}}` for failures
- `db.add()` is synchronous in SQLAlchemy async sessions — tests use `MagicMock` not `AsyncMock` for this call

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing aiohttp, urllib3, psutil in venv for node.py tests**
- **Found during:** Task 1 (TDD RED phase)
- **Issue:** node.py imports `aiohttp`, `urllib3`, `psutil` which were absent from the dev venv — test collection failed on `ModuleNotFoundError`
- **Fix:** Ran `pip install aiohttp urllib3` in `.venv`
- **Files modified:** None (dev environment only)
- **Verification:** All 7 node tests collected and ran
- **Committed in:** Not committed (venv only)

**2. [Rule 1 - Bug] Fixed test mock: `db.add()` is sync, must use `MagicMock` not `AsyncMock`**
- **Found during:** Task 2 (TDD GREEN phase)
- **Issue:** `AsyncMock.add.side_effect` fires but emits "coroutine never awaited" warning; captured list remained empty because the coroutine return wasn't being processed
- **Fix:** Override `mock_db.add = MagicMock(side_effect=...)` in `_make_mock_db()` helper
- **Files modified:** `puppeteer/tests/test_execution_record.py`
- **Verification:** All 10 integration tests pass with correct ExecutionRecord assertions
- **Committed in:** `ee247eb` (Task 2 feat commit)

---

**Total deviations:** 2 auto-fixed (1 blocking environment, 1 test mock bug)
**Impact on plan:** Both fixes necessary for test execution. No scope creep. Production code was correct on first attempt.

## Issues Encountered
- Pre-existing import failures in `test_main.py`, `test_sprint3.py`, `test_bootstrap_admin.py`, `test_intent_scanner.py`, `test_tools.py` — these predate this plan and are out of scope per CLAUDE.md "Known Deferred Issues"

## User Setup Required
None — no external service configuration required. The `execution_records` table is created by `create_all` at startup (new table, no ALTER needed). For existing Postgres deployments, `migration_v14.sql` (from Plan 01-01) already covers the table creation.

## Next Phase Readiness
- Pipeline write path is complete: node sends structured output, server persists ExecutionRecord
- Plan 03 (main.py GET /executions/{guid} route) can now query execution_records rows
- No blockers for Plan 03

## Self-Check: PASSED

- puppets/environment_service/node.py: FOUND
- puppeteer/agent_service/services/job_service.py: FOUND
- puppets/environment_service/tests/test_output_log.py: FOUND
- puppeteer/tests/test_execution_record.py: FOUND
- Commit 842cc8d (Task 1 RED): FOUND
- Commit 47a95cc (Task 1 GREEN): FOUND
- Commit c4fed47 (Task 2 RED): FOUND
- Commit ee247eb (Task 2 GREEN): FOUND

---
*Phase: 01-output-capture*
*Completed: 2026-03-04*
