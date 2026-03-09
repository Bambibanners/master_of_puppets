# Phase 2: Conditional Logic & Signal Dispatch - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 focuses on **Reactive Orchestration**. It moves beyond static time-based or sequence-based scheduling into dynamic workflow management.

**In Scope:**
- Database schema for `Signal` tracking.
- Schema update for `Job.depends_on` to support complex conditions.
- API for firing signals (`POST /api/signals/{name}`).
- Hardened unblocking engine supporting Job Statuses and Signals.

**Out of Scope:**
- Signal versioning.
- Time-to-live (TTL) for signals (Phase 3 candidate).
- Wait-timeout for blocked jobs (if signal never arrives).

</domain>

<decisions>
## Implementation Decisions

### Signal Persistence
- **Table**: `signals`.
- **Primary Key**: `name`.
- **Payload**: Stored as JSON to allow external systems to pass metadata through the signal.

### Dependency Evaluation
- **Strategy**: On any terminal state change (Job or Signal), the system scans for `BLOCKED` jobs that *might* be affected.
- **Search**: Continue using `LIKE` queries on the `depends_on` column for simplicity in Phase 2, but refine the pattern matching to handle the new JSON object structure.

### Backward Compatibility
- Ensure that existing `depends_on` lists (plain GUID strings) continue to function exactly as they do today (unblock on COMPLETED).

</decisions>

<specifics>
## Specific Ideas

- The `Signal` API should return the number of jobs that were unblocked by the signal.
- In the UI, show a "Waiting for Signal: name" badge.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `JobService._unblock_dependents`: To be refactored.
- `JobService.report_result`: The trigger point for completion-based unblocking.
- `require_permission` for API security.

### Integration Points
- `puppeteer/agent_service/db.py`: `Signal` table.
- `puppeteer/agent_service/services/job_service.py`: Core logic expansion.
- `puppeteer/agent_service/main.py`: New Signal endpoints.
- `puppeteer/dashboard/src/views/Jobs.tsx`: UI visualization.

</code_context>

---

*Phase: 02-conditional-triggers*
*Context gathered: 2026-03-05*
