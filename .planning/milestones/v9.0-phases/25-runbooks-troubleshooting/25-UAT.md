---
status: complete
phase: 25-runbooks-troubleshooting
source: [25-01-SUMMARY.md, 25-02-SUMMARY.md, 25-03-SUMMARY.md, 25-04-SUMMARY.md]
started: 2026-03-17T17:00:00Z
updated: 2026-03-17T17:05:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Runbooks Nav Entries in mkdocs.yml
expected: Four entries under Runbooks nav in mkdocs.yml — Node Troubleshooting, Job Execution, Foundry, FAQ — pointing to runbooks/nodes.md, runbooks/jobs.md, runbooks/foundry.md, runbooks/faq.md.
result: pass

### 2. Runbooks Overview Page (index.md)
expected: Real overview page (not a stub) with guide table linking all four runbooks and symptom-first framing ("Find the observable state that matches what you are seeing").
result: pass

### 3. Node Troubleshooting — Quick Reference Jump Table
expected: Quick Reference table at the top of nodes.md with ~10 rows, each symptom linking to the corresponding H3 section.
result: pass

### 4. Node Troubleshooting — Enrollment Failures Coverage
expected: ~5 H3 symptom sections under Enrollment Failures, each with root cause paragraph, numbered recovery steps, Verify bash block with expected output, and escalation note.
result: pass

### 5. Node Troubleshooting — Heartbeat Loss and Certificate Errors
expected: Heartbeat Loss cluster (~3 H3s) and Certificate Errors cluster (~2 H3s) with exact log strings from node.py in fenced code blocks and cross-links to mtls.md.
result: pass

### 6. Job Execution Troubleshooting — Quick Reference and Dispatch Failures
expected: Quick Reference jump table with 10 symptoms; Dispatch Failures cluster with H3s for PENDING, BLOCKED, CANCELLED, DEAD_LETTER (danger admonition: cannot be retried), ZOMBIE_REAPED.
result: pass

### 7. Job Execution Troubleshooting — Signing Errors Cluster
expected: 3 H3 symptom sections for SECURITY_REJECTED variants with exact log strings from node.py/job_service.py and cross-links to mop-push.md#ed25519-key-setup.
result: pass

### 8. Foundry Troubleshooting Runbook
expected: Quick Reference table; Build Failures (4 H3s), Smelt-Check Failures (2 H3s), Registry Issues (2 H3s). Exact log strings from foundry_service.py in fenced code blocks.
result: pass

### 9. Operator FAQ — Required Gotchas
expected: 4 required gotchas: blueprint dict format, EXECUTION_MODE=direct for DinD, JOIN_TOKEN structure, ADMIN_PASSWORD seed-only. Quick Reference table at top.
result: pass

### 10. Operator FAQ — Ed25519 Signing Bypass Entry
expected: FAQ entry with danger admonition explicitly stating no flag, env var, or API option exists to disable signature verification.
result: pass

### 11. mkdocs --strict Build Passes
expected: All nav entries resolve to existing files; no broken links cause strict-mode failures. SUMMARY files report build passes.
result: pass

## Summary

total: 11
passed: 11
issues: 0
pending: 0
skipped: 0

## Gaps

[none]
