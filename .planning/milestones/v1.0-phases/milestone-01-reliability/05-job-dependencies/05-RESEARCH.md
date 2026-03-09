# Phase 5: Job Dependencies - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 5 introduces job orchestration through task chaining. It allows defining a Directed Acyclic Graph (DAG) of jobs where a job only starts when its upstreams have successfully completed.

## Data Model Changes
- **`Job` Table**: Needs a `depends_on` column. 
    - Decision: Store as a JSON list of GUIDs for simplicity and consistency with `target_tags`.
- **`Job` Status**: Needs a new state: `BLOCKED`.
    - `BLOCKED`: Job is waiting for one or more upstream jobs to reach `COMPLETED`.

## Core Logic: Blocked State & Unblocking
1.  **Submission**:
    - When a job is submitted via `create_job`:
        - Validate that all `depends_on` GUIDs exist in the `jobs` table.
        - Perform cycle detection (see below).
        - Check current status of upstreams.
        - If any upstream is not `COMPLETED`, set job status to `BLOCKED`.
        - Else, set to `PENDING`.
2.  **Unblocking (Triggered by Upstream Completion)**:
    - In `JobService.report_result`, when a job reaches `COMPLETED`:
        - Find all jobs where `guid` is in their `depends_on` list AND status is `BLOCKED`.
        - For each dependent job:
            - Check if ALL of its upstreams are now `COMPLETED`.
            - If yes, transition job status from `BLOCKED` to `PENDING`.
3.  **Failure Handling**:
    - If an upstream job fails terminaly (`FAILED` non-retriable or `DEAD_LETTER`), what happens to downstream jobs?
    - Option A: Downstream jobs stay `BLOCKED` forever (deadlock).
    - Option B: Transition downstream jobs to `CANCELLED` (preferred for visibility).
    - Decision: Requirement DEP-01 says "until all upstream jobs show COMPLETED status". If one fails, it will never be completed. I will implement a "Cancel Downstream" logic where terminal failure of an upstream cancels its immediate dependents.

## Cycle Detection
- Use a simple Depth First Search (DFS) when creating a job.
- Since a job only depends on *existing* jobs, a new job cannot create a cycle unless it depends on itself (trivial check) or its GUID was somehow known beforehand.
- Wait, the requirement says "detects and rejects cycles at creation time". If I create job A, then job B depends on A, then job C depends on B... this is always a DAG.
- Cycles can only occur if we allow *updating* dependencies of existing jobs.
- If we only support dependencies at *creation time*, cycles are impossible because you can only depend on jobs that already exist.
- *Self-correction*: If we support `ScheduledJob` dependencies (Blueprint level), cycles ARE possible.
- However, for Phase 5 initial implementation, we focus on ad-hoc jobs (`Job` table).

## Dashboard Integration
- `JobDetailPanel.tsx`: Show a "Dependencies" section.
- List which jobs are blocking the current job.
- Status Badge: Add `BLOCKED` color (Zinc/Outline with custom icon).

## Pitfalls
- **Performance**: Large-scale dependency unblocking. In `report_result`, searching for dependents via JSON column (`LIKE '%guid%'`) is slow.
- *Solution*: For Phase 5, simple `LIKE` or manual loop is fine. For scale, a junction table is mandatory.
- **Race Conditions**: Two upstreams completing simultaneously might both try to unblock the same job. SQLAlchemy's session management should handle this, but explicit locking or `SELECT FOR UPDATE` might be needed for the unblocking check.

## Proposed Plans
- **Plan 5.1**: DB & Models. Add `depends_on` to `Job` ORM and `JobCreate`/`JobResponse` Pydantic models. Add `BLOCKED` and `CANCELLED` statuses.
- **Plan 5.2**: Submission & Cycle Detection. Implement dependency validation and cycle detection in `JobService.create_job`.
- **Plan 5.3**: Unblocking Logic. Implement the trigger in `report_result` to transition `BLOCKED` jobs to `PENDING` (or `CANCELLED` on failure).
- **Plan 5.4**: Dashboard UI. Add dependency visualization to the job detail pane and support dependency selection in the job creation flow.

---
*Phase: 05-job-dependencies*
*Context: Master of Puppets Reliability Milestone*
