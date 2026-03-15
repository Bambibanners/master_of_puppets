---
phase: 19-dashboard-staging-view-and-governance-doc
plan: "01"
subsystem: ui
tags: [react, typescript, job-definitions, staging, lifecycle, badges]

# Dependency graph
requires:
  - phase: 17-backend-oauth-device-flow-and-job-staging
    provides: status field on ScheduledJob, pushed_by field, DRAFT/ACTIVE/DEPRECATED/REVOKED lifecycle states
provides:
  - Status-aware badge renderer for job lifecycle states (DRAFT/ACTIVE/DEPRECATED/REVOKED)
  - Tabbed ACTIVE / STAGING view in JobDefinitions page
  - pushed_by attribution display per job row
  - Expandable script inspection panel per job row
  - Publish (DRAFT -> ACTIVE) action button
affects: [19-02, 19-03, 19-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Button-based tab toggle with filteredDefinitions derived state — no external tab library needed"
    - "renderStatusBadge() switch mapping lifecycle state strings to Tailwind colour variants"

key-files:
  created: []
  modified:
    - puppeteer/dashboard/src/views/JobDefinitions.tsx
    - puppeteer/dashboard/src/components/job-definitions/JobDefinitionList.tsx

key-decisions:
  - "Button-based toggle over Radix Tabs — simpler, consistent with existing design system usage in this page, no new dependency"
  - "filteredDefinitions derived at render time from activeTab state — avoids duplicate API calls"
  - "DRAFT jobs shown exclusively in Staging tab; ACTIVE/DEPRECATED/REVOKED in Active tab — clean separation"
  - "Publish button uses PATCH /jobs/definitions/{id} with { status: 'ACTIVE' } — reuses existing update endpoint, no new route needed"
  - "Script inspection as expandable TableRow below the definition — keeps table compact while allowing inline inspection"

patterns-established:
  - "Status badge pattern: renderStatusBadge() centralises colour mapping; extend by adding new case to switch"
  - "Tab filter pattern: activeTab state + filteredDefinitions derived list — avoids multiple API calls"

requirements-completed: []

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 19 Plan 01: UI Foundation Summary

**Status badges (DRAFT/ACTIVE/DEPRECATED/REVOKED), tabbed ACTIVE/STAGING view, and pushed_by attribution added to the Job Definitions dashboard page**

## Performance

- **Duration:** 5 min (work already in working tree)
- **Started:** 2026-03-15T15:28:09Z
- **Completed:** 2026-03-15T15:30:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- Status-aware badge renderer maps all four lifecycle states to distinct colour treatments (green/yellow/zinc/red)
- Tabbed ACTIVE/STAGING toggle filters the definitions list without additional API calls
- pushed_by attribution shown inline below job name for CLI-pushed jobs
- Expandable row reveals full script source for inline inspection
- Publish button on DRAFT rows promotes job to ACTIVE via existing PATCH endpoint

## Task Commits

Each task was committed atomically:

1. **Task 1-3: All three tasks (interfaces, badges, tabbed view)** - `8c0ce03` (feat)

**Plan metadata:** (pending docs commit)

## Files Created/Modified
- `puppeteer/dashboard/src/views/JobDefinitions.tsx` - Added activeTab state, filteredDefinitions, handlePublish, button-based tab toggle, passed onPublish prop to JobDefinitionList
- `puppeteer/dashboard/src/components/job-definitions/JobDefinitionList.tsx` - Added status/pushed_by to JobDefinition interface, renderStatusBadge(), Status column, expandable script row, Send button for DRAFT jobs

## Decisions Made
- Button-based tab toggle over Radix Tabs — avoids new dependency and is consistent with existing button patterns in the UI
- filteredDefinitions derived at render time — keeps data flow simple, single API call serves both tabs
- Publish action reuses existing PATCH endpoint with `{ status: 'ACTIVE' }` — no new backend route required

## Deviations from Plan
None - plan executed exactly as written. Work was already present in the working tree; this summary documents the implementation and records the commit.

## Issues Encountered
None — implementation was already complete in the working tree prior to this execution.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Status badges and tabbed view are live; Plans 19-02 and 19-03 can build on these foundations
- The DRAFT/ACTIVE filter is the prerequisite for the staging workflow demonstrated in Plan 19-04

---
*Phase: 19-dashboard-staging-view-and-governance-doc*
*Completed: 2026-03-15*
