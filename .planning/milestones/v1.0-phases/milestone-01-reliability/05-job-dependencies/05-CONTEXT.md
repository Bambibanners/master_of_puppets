# Phase 5: Job Dependencies - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 transitions the system from independent task execution to orchestrated job flows (DAGs). It introduces the concept of a `BLOCKED` state where a job exists in the database but is ineligible for assignment until its upstream requirements are met.

This phase focuses on ad-hoc `Job` dependencies. Integration with `ScheduledJob` (templates) is considered for a future enhancement but may be touched upon if necessary for requirement parity.

</domain>

<decisions>
## Implementation Decisions

### Dependency Storage
- **Column**: `depends_on` in the `jobs` table.
- **Format**: JSON string representing a list of GUIDs: `["guid-1", "guid-2"]`.
- **Rationale**: Keeps the schema flat and consistent with existing patterns for `target_tags` and `capability_requirements`.

### State Transitions
- **Initial State**: If `depends_on` is provided and not empty, the job starts as `BLOCKED`.
- **Unblocking Trigger**: Occurs within the `report_result` transaction when a job reaches `COMPLETED`.
- **Downstream Failure**: If an upstream job fails terminaly (`DEAD_LETTER` or non-retriable `FAILED`), all jobs directly depending on it transition to `CANCELLED` to avoid persistent deadlocks.

### Cycle Detection
- **Enforcement**: Strictly at creation time.
- **Logic**: Since dependencies can only be established against *pre-existing* jobs in this phase, cycles are technically impossible (you can't depend on a job that doesn't have a GUID yet). However, we will implement a validation check to ensure no self-dependency and that all referenced GUIDs exist.

### Dashboard UX
- **Job Detail**: A new section showing "Waitings For" (Upstreams) and "Blocks" (Downstreams).
- **Status Indicator**: `BLOCKED` status badge with a "Lock" icon.
- **Interactive Submission**: Allow users to paste/select GUIDs of existing jobs when submitting a new job.

</decisions>

<specifics>
## Specific Ideas

- The `BLOCKED` status should be visually distinct from `PENDING` (which means "ready to run but no node available").
- When a job is `BLOCKED`, the detail panel should highlight which specific GUIDs are still in non-completed states.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `JobService.report_result`: The central point for state updates.
- `JobResponse`: Already handles many optional fields.
- `mask_secrets`: Used during list/detail views.

### Integration Points
- `puppeteer/agent_service/db.py`: Add `depends_on` to `Job`.
- `puppeteer/agent_service/services/job_service.py`: 
    - Update `create_job` for dependency validation.
    - Update `report_result` for unblocking logic.
- `puppeteer/dashboard/src/views/Jobs.tsx`: Update status badge and detail panel.
- `puppeteer/migration_v18.sql`: Schema update.

</code_context>

---

*Phase: 05-job-dependencies*
*Context gathered: 2026-03-05*
