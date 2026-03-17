---
phase: 25-runbooks-troubleshooting
plan: "03"
subsystem: docs
tags: [mkdocs, runbooks, troubleshooting, jobs, signing, ed25519]

requires:
  - phase: 25-01
    provides: stub files and nav entries for runbooks section, enabling strict-mode builds

provides:
  - Full job execution troubleshooting runbook at docs/docs/runbooks/jobs.md
  - Quick Reference jump table covering 10 observable symptoms
  - Dispatch Failures cluster: PENDING, BLOCKED, CANCELLED, DEAD_LETTER, ZOMBIE_REAPED
  - Signing Errors cluster: SECURITY_REJECTED (3 variants — sig failed, key missing, missing sig)
  - Timeout Patterns cluster: zombie reaper, stuck ASSIGNED
  - Exact verbatim log strings from node.py and job_service.py in fenced code blocks
  - Cross-links to mop-push.md#ed25519-key-setup and faq.md

affects:
  - 25-04 (faq.md — jobs.md cross-links to faq.md; FAQ content can reference jobs.md)
  - Any phase that writes Foundry or node runbooks (established H2-cluster + H3-symptom pattern)

tech-stack:
  added: []
  patterns:
    - "H2-cluster + H3-symptom runbook pattern: each H3 has root cause (2 sentences), numbered recovery steps, Verify step, escalation note"
    - "Quick Reference jump table at top of each runbook page — symptom column links to H3 anchors"
    - "Exact log strings in fenced code blocks: operators match what they see to the section"
    - "danger admonition for irreversible states (DEAD_LETTER cannot be retried); warning for security-adjacent notes"

key-files:
  created:
    - docs/docs/runbooks/jobs.md
  modified: []

key-decisions:
  - "Zombie reaper (zombie_timeout_minutes, default 30 min, configurable) documented as the effective operator-visible timeout — the 30-second direct-subprocess path is legacy/fallback and not documented as a primary timeout"
  - "DEAD_LETTER carries a danger admonition (cannot be retried — must resubmit new job) to prevent operator confusion about in-place retry"
  - "BLOCKED treated as expected behaviour with no action needed when dependency is in-flight — escalation only when dependency is FAILED or DEAD_LETTER"
  - "See Also section at bottom links to mop-push guide and faq.md for operator who wants broader context"

patterns-established:
  - "H2 cluster groups observable-state symptoms; H3 uses symptom or exact log line as header — matches 25-CONTEXT.md locked structure"
  - "Admonitions placed before/after numbered lists, never inside them — avoids MkDocs list-counter reset"
  - "Verify step uses expected-output prose (not just a command) so operators know what success looks like"

requirements-completed:
  - RUN-02

duration: 1min
completed: "2026-03-17"
---

# Phase 25 Plan 03: Job Execution Troubleshooting Runbook Summary

**Symptom-first job runbook with 10 H3 sections across 3 failure clusters — exact log strings from node.py and job_service.py enable operators to match their terminal output directly to the recovery section**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-17T16:29:19Z
- **Completed:** 2026-03-17T16:34:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Wrote full `docs/docs/runbooks/jobs.md` replacing the Wave 1 stub (3 lines → 258 lines)
- 10 symptom H3s covering every relevant job status value: `PENDING`, `BLOCKED`, `CANCELLED`, `DEAD_LETTER`, `ZOMBIE_REAPED`, `SECURITY_REJECTED` (3 variants)
- All 5 exact log strings from the `<interfaces>` block appear verbatim in fenced code blocks, including the cancellation propagation log and all three signing error messages
- Zombie reaper correctly documented as the effective timeout mechanism; 30-second subprocess fallback intentionally omitted per plan guidance

## Task Commits

1. **Task 1: Write jobs.md — full job execution troubleshooting runbook** - `1aaa813` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `docs/docs/runbooks/jobs.md` — Full runbook: Quick Reference jump table, Dispatch Failures cluster (5 H3s), Signing Errors cluster (3 H3s), Timeout Patterns cluster (2 H3s), See Also links

## Decisions Made

- Zombie reaper (configurable `zombie_timeout_minutes`) documented as the operator-visible timeout, not the 30-second direct-subprocess path. The plan's `<interfaces>` block and RESEARCH.md open question both recommended this approach — the subprocess path is a legacy fallback, not the normal execution flow.
- `DEAD_LETTER` given a `!!! danger` admonition ("cannot be retried — must resubmit") to preempt the most common operator confusion about that status.
- `BLOCKED` framed as expected behaviour (not a failure) with a clear decision tree in prose: wait if dependency is running, escalate only if dependency is FAILED/DEAD_LETTER.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `jobs.md` is complete and cross-links to `faq.md` — ready for Plan 25-04 (FAQ) which can reference jobs.md symptom sections
- `mkdocs build --strict` will pass: no new nav entries added (stub file was already registered in nav by Plan 25-01), file content uses only configured MkDocs extensions

---
*Phase: 25-runbooks-troubleshooting*
*Completed: 2026-03-17*
