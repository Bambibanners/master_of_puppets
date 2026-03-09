# Phase 2: Conditional Logic & Signal Dispatch - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 2 extends the job dependency engine from simple sequential completion (`Job A -> Job B`) to complex conditional logic and external signals. This allows MOP to act as a reactive orchestrator where jobs can wait for human approval, external system events, or specific failure outcomes of previous tasks.

## Existing Implementation
- **Job Dependencies**: Sequential completion only. `BLOCKED` status until all upstreams are `COMPLETED`.
- **Trigger System**: Immediate job firing via authenticated slugs.

## Requirements Analysis
- **Signals**: Jobs must be able to wait for a named event (e.g., `release-authorized`) that isn't bound to a specific job GUID.
- **Outcomes**: Dependencies should support conditions like "Wait for Job A to FAIL" or "Wait for Job A to reach ANY terminal state".
- **External Integration**: Systems need a way to "fire" these signals securely.

## Proposed Strategy: Signals & Conditionals

### 1. Signal Abstraction
A `Signal` is a lightweight, named event persisted in the database.
- Table: `signals`
- Fields: `name` (unique), `payload` (JSON), `created_at`.

### 2. Flexible Dependency Schema
Migrate `depends_on` from `List[str]` (GUIDs) to `List[Union[str, Dict]]`.
- String (Legacy): `GUID` -> wait for GUID to be `COMPLETED`.
- Object (New):
    - Job dependency: `{"type": "job", "ref": "GUID", "condition": "COMPLETED" | "FAILED" | "ANY"}`
    - Signal dependency: `{"type": "signal", "ref": "NAME"}`

### 3. Orchestration Logic
- `JobService.report_result` must handle both `COMPLETED` and `FAILED` transitions to check for conditional dependents.
- A new `SignalService` will handle signal firing and subsequent unblocking checks.

### 4. Authentication
Signals should be fireable by:
- **Admins** (interactive).
- **Service Principals** (via API keys).

## Potential Pitfalls
- **Signal Lifetime**: Should a signal persist forever? For Phase 2, yes. Future refinement might include TTL.
- **Performance**: Large-scale dependency checking on signal fire. Need efficient indexing on `status='BLOCKED'`.

## Implementation Plan
- **Plan 02-01**: DB & Models. Add `signals` table and update `depends_on` data handling.
- **Plan 02-02**: Signal API. `POST /api/signals/{name}` with SP authentication.
- **Plan 02-03**: Core Engine Hardening. Refactor `_unblock_dependents` to handle conditions and signals.
- **Plan 02-04**: Dashboard UI. Visual indicators for signal dependencies and outcome conditions.

---
*Phase: 02-conditional-triggers*
*Context: Master of Puppets Automation Milestone*
