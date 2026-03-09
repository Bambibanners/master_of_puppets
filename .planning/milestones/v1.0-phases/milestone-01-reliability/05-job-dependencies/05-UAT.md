---
status: pending
phase: 05-job-dependencies
source: 05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md
started: 2026-03-05T17:15:00Z
updated: 2026-03-05T17:15:00Z
---

## Current Test

[Testing complete]

## Tests

### 1. Submission with dependencies starts as BLOCKED
expected: POST /jobs with a valid `depends_on` list referencing a non-completed job should result in the new job having status `BLOCKED`.
result: pass
note: Logic in create_job correctly identifies incomplete upstreams and assigns BLOCKED status.

### 2. Automatic unblocking on COMPLETED
expected: When all jobs in a `BLOCKED` job's `depends_on` list reach `COMPLETED` status, the blocked job should transition to `PENDING`.
result: pass
note: _unblock_dependents helper correctly unblocks jobs once the last dependency completes.

### 3. Fan-in logic (Multiple dependencies)
expected: A job with multiple upstreams stays `BLOCKED` until ALL upstreams are `COMPLETED`. It should NOT start if only a subset are finished.
result: pass
note: _unblock_dependents performs an 'all' check across all referenced GUIDs.

### 4. Failure propagation (Upstream terminal failure)
expected: If an upstream job fails terminally (`DEAD_LETTER`, non-retriable `FAILED`, or `SECURITY_REJECTED`), its immediate downstream blocked jobs should transition to `CANCELLED`.
result: pass
note: _cancel_dependents implemented and integrated into report_result for all terminal failure states. Supports recursive propagation.

### 5. Cycle Detection (Self-dependency)
expected: Attempting to create a job that depends on its own future GUID or a non-existent GUID should return an error. (Note: Self-ref is impossible via API as GUID is assigned server-side, but check for 400 on missing GUIDs).
result: pass
note: create_job raises 400 if any dependency GUID does not exist in the database.

### 6. Dashboard Visualization
expected: The Jobs dashboard shows a `BLOCKED` badge for blocked jobs. The detail panel shows the list of upstream GUIDs under a "Depends On" section.
result: pass
note: UI updated with Lock/Ban icons and a clear Depends On list in the detail pane.

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

<!-- None identified yet -->
