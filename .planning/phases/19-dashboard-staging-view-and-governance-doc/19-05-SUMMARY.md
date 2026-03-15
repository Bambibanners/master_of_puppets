---
phase: 19-dashboard-staging-view-and-governance-doc
plan: 05
subsystem: api
tags: [fastapi, scheduler, job-definitions, status-lifecycle]

# Dependency graph
requires:
  - phase: 19-04
    provides: E2E verification confirming DASH-04 bug exists and needs fixing
provides:
  - update_job_definition() correctly persists status changes to the database
  - PATCH /jobs/definitions/{id} with {status: 'ACTIVE'} now promotes DRAFT jobs to ACTIVE
affects: [scheduler_service, job-definitions-api, dashboard-publish-button]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - puppeteer/agent_service/services/scheduler_service.py

key-decisions:
  - "No new validation needed in service layer: upstream REVOKED gate in main.py already blocks invalid transitions before reaching update_job_definition()"

patterns-established: []

requirements-completed: [DASH-04]

# Metrics
duration: 4min
completed: 2026-03-15
---

# Phase 19 Plan 05: Status Assignment Gap Closure Summary

**One-line fix closes DASH-04: `update_job_definition()` now writes `update_req.status` to `job.status` so PATCH /jobs/definitions/{id} with `{status: 'ACTIVE'}` actually persists the promotion**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-15T15:51:56Z
- **Completed:** 2026-03-15T15:55:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Identified the missing line in `update_job_definition()`: all other optional fields (name, schedule_cron, target_tags, etc.) followed the `if update_req.X is not None: job.X = update_req.X` guard pattern, but `status` was absent despite being defined on `JobDefinitionUpdate`
- Added `if update_req.status is not None: job.status = update_req.status` at line 281, immediately after the `timeout_minutes` block and before the `job.updated_at` timestamp assignment
- Verified syntax with `python3 -m py_compile` — no errors introduced

## Task Commits

1. **Task 1: Apply status field assignment in update_job_definition** - `0296e25` (fix)

## Files Created/Modified
- `puppeteer/agent_service/services/scheduler_service.py` - Added status field assignment in `update_job_definition()` (2 lines: guard + assignment)

## Decisions Made
No new decisions required — the fix follows the existing guard pattern already used for every other optional field in the same method. No upstream validation changes needed because the REVOKED gate in `main.py` already rejects invalid status transitions before the service layer is reached.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `python3 -c "import agent_service.services.scheduler_service"` failed with `ModuleNotFoundError: No module named 'sqlalchemy'` — pre-existing environment issue (SQLAlchemy only installed inside the Docker container, not on the host). Used `python3 -m py_compile` for syntax validation instead. Not a regression.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- DASH-04 gap is fully closed: the Publish button flow (PATCH with `{status: 'ACTIVE'}`) now persists to the DB
- Phase 19 is complete: all five plans executed (status UI badges, staging tab, publish button, E2E verification, DASH-04 fix)

---
*Phase: 19-dashboard-staging-view-and-governance-doc*
*Completed: 2026-03-15*
