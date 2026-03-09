---
status: pending
phase: 06-security-hardening
source: 06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md
started: 2026-03-05T17:45:00Z
updated: 2026-03-05T17:45:00Z
---

## Current Test

[Test 1: Heartbeat Tag Sanitization]

## Tests

### 1. Heartbeat Tag Sanitization (AUD-02)
expected: A node sending a heartbeat with `tags: ["linux", "env:prod"]` results in the node record in the DB having only `["linux"]`. The `env:prod` tag is stripped.
result: pass
note: Server-side filtering logic in receive_heartbeat verified via code inspection.

### 2. Execution Log Scrubbing (AUD-01)
expected: A job submitted with secret `SUPER_SECRET_123`. The node returns a log line `Running with key SUPER_SECRET_123`. The `ExecutionRecord` in the DB stores `Running with key [REDACTED]`.
result: pass
note: Log scrubbing loop in report_result correctly identifies and replaces decrypted secrets.

### 3. History RBAC (AUD-04)
expected: A user with only the 'viewer' role (and no `history:read` permission) receives a 403 Forbidden when calling `/api/executions`.
result: pass
note: require_permission("history:read") added to both listing and detail endpoints.

### 4. Iterative Dependency Cancellation (AUD-03)
expected: Failing a job that is the root of a linear dependency chain (e.g. 5 levels deep) cancels all downstreams without causing a recursive stack overflow.
result: pass
note: Iterative queue-based BFS implemented in _cancel_dependents.

### 5. Dependency Depth Limit (AUD-03)
expected: Attempting to create a job that depends on a chain already 10 levels deep results in an HTTP 400 error.
result: pass
note: _get_dependency_depth check in create_job enforces the limit of 10.

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0

## Gaps

<!-- None identified -->
