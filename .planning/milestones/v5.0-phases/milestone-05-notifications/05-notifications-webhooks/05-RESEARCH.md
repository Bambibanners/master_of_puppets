# Phase 05-01 Research: Alerting Infrastructure

## Current State Analysis

### 1. Job Failures
- Jobs currently transition through `PENDING` -> `ASSIGNED` -> `COMPLETED` or `FAILED`.
- The `RetryPolicy` (RETR-01) logic needs to be verified. If it exists, where is the "exhausted" state handled?
- We need to find the point where a job is moved to `DEAD_LETTER` or simply marked `FAILED` with 0 retries left.

### 2. Node Health
- Nodes poll the `/heartbeat` endpoint.
- There is likely a "last seen" timestamp in the `Node` model.
- We need to identify if there's an existing background task that reaps "dead" nodes or if it's currently only reactive.

### 3. Existing "Alerts" or "Audit Logs"
- Does a `Notification` or `Alert` table already exist as a stub?
- How are `AuditLog` entries created? Can we reuse that pattern?

## Research Tasks
1. Search `db.py` for `Alert`, `Notification`, or `AuditLog`.
2. Examine `job_service.py` for failure handling logic.
3. Check `main.py` for heartbeat processing and node status updates.
4. Verify current `RetryPolicy` implementation details.

## Findings (To be populated)
- [ ] Job terminal failure location:
- [ ] Node offline detection mechanism:
- [ ] Alerting schema design:
