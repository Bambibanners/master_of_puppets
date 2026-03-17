---
phase: 25-runbooks-troubleshooting
plan: "04"
subsystem: documentation
tags: [mkdocs, runbooks, foundry, faq, troubleshooting]

requires:
  - phase: 25-01
    provides: stub files and nav entries for runbooks/foundry.md and runbooks/faq.md
  - phase: 23-getting-started-core-feature-guides
    provides: foundry.md feature guide with confirmed anchors for cross-linking
  - phase: 24-extended-feature-guides-security
    provides: mtls.md and air-gap.md security guides used as cross-link targets

provides:
  - Foundry troubleshooting runbook with Quick Reference, 3 H2 clusters, 8 H3 symptoms
  - Unified FAQ with 10 entries covering all 4 required gotchas and 3 required how-tos
  - Verbatim log strings from foundry_service.py embedded in code blocks for operator matching

affects: [phase-25-final-verification, any-operator-facing-docs-update]

tech-stack:
  added: []
  patterns:
    - Symptom-first H3 headers with root-cause + numbered-recovery + verify + escalation structure
    - Quick Reference jump table at top of each runbook for crisis navigation
    - Verbatim log string embedding in code blocks for operator search matching
    - Danger admonition for security invariants that cannot be bypassed (Ed25519 signing)
    - Warning admonition for irreversible destructive actions (drop DB)

key-files:
  created: []
  modified:
    - docs/docs/runbooks/foundry.md
    - docs/docs/runbooks/faq.md

key-decisions:
  - "Foundry runbook clusters mirror the failure surface exactly: Build Failures / Smelt-Check Failures / Registry Issues — matching how operators observe failures in the dashboard"
  - "FAQ entries use plain H3 statements (not questions in backtick headers) to ensure reliable anchor generation"
  - "Ed25519 signing FAQ entry uses danger admonition with explicit wording that no flag/env/API option exists to disable verification"
  - "ADMIN_PASSWORD entry directs to dashboard Reset Password flow with warning admonition against dropping the DB"

patterns-established:
  - "Runbook Quick Reference: symptom column + anchor link column, one row per H3"
  - "FAQ Quick Reference: question column + anchor link column, one row per H3"
  - "Escalation pattern: verify step + if-still-failing fallback in every H3 section"

requirements-completed: [RUN-03, RUN-04]

duration: 3min
completed: 2026-03-17
---

# Phase 25 Plan 04: Foundry Troubleshooting and FAQ Summary

**Foundry troubleshooting runbook with 8 symptom H3s (build failures, Smelt-Check, registry) and unified FAQ with 10 entries covering all required gotchas and how-tos — mkdocs --strict build passes.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-17T16:29:18Z
- **Completed:** 2026-03-17T16:32:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Wrote `docs/docs/runbooks/foundry.md` — complete Foundry troubleshooting runbook (193 lines): Quick Reference jump table, Build Failures cluster (4 H3s), Smelt-Check Failures cluster (2 H3s), Registry Issues cluster (2 H3s). All exact log strings from `foundry_service.py` appear verbatim in fenced code blocks.
- Wrote `docs/docs/runbooks/faq.md` — unified operator FAQ (133 lines): 10 H3 entries including all 4 required gotchas (blueprint dict format, EXECUTION_MODE=direct, JOIN_TOKEN structure, ADMIN_PASSWORD seed-only) and all 3 required how-tos (node identity reset, UTC timezone, Ed25519 signing cannot be bypassed). Danger admonition on signing entry explicitly states no bypass exists.
- Docker `mkdocs build --strict` passes for the complete docs image.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write foundry.md — Foundry troubleshooting runbook** - `b493585` (feat)
2. **Task 2: Write faq.md — unified operator FAQ** - `22a5beb` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `docs/docs/runbooks/foundry.md` — Complete Foundry troubleshooting runbook replacing stub; 193 lines, 8 symptom H3s across 3 H2 clusters
- `docs/docs/runbooks/faq.md` — Complete unified operator FAQ replacing stub; 133 lines, 10 H3 entries with Quick Reference jump table

## Decisions Made

- FAQ H3 headers are plain statements (not questions in code spans) — anchor generation is unreliable with backtick-wrapped headers; cross-links to anchors work reliably with plain text H3s
- Foundry runbook kept the three cluster names from the plan (Build Failures / Smelt-Check Failures / Registry Issues) as they map directly to how operators observe failures in the Templates view
- Warning admonition added to ADMIN_PASSWORD entry explicitly calling out that dropping the database destroys all operational data — this gotcha has caught real operators before

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 25 Wave 2 content plans (25-02 nodes.md, 25-03 jobs.md, 25-04 foundry.md, faq.md) are all complete.
- All four runbook files are fully written; mkdocs --strict build passes.
- Phase 25 finalization can proceed (update runbooks/index.md overview page if planned).

---
*Phase: 25-runbooks-troubleshooting*
*Completed: 2026-03-17*
