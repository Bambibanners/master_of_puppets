# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-04)

**Core value:** Jobs run reliably — on the right node, when scheduled, with output captured — without weakening the security model.
**Current focus:** Phase 1 — Output Capture

## Current Position

Phase: 1 of 5 (Output Capture)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-03-04 — Roadmap created; all 20 v1 requirements mapped to 5 phases

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: none yet
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: Phase order is strictly data-constrained — OUT → RETR → HIST → TAG → DEP
- Roadmap: Retry (Phase 2) and zombie reaper ship together — reaper is mandatory, not deferred
- Roadmap: Output stored in separate `execution_records` table, never in `jobs.result` (prevents list-endpoint bloat)
- Roadmap: Dependency evaluation runs inside `pull_work`, not a background poller (eliminates TOCTOU race)

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 2: APScheduler `misfire_grace_time` defaults to 1s — high-frequency jobs may be silently skipped under load. Validate `scheduler_service.py` before Phase 2 ships.
- Phase 2: SQLite does not support `ALTER TABLE ... IF NOT EXISTS` — confirm dev teardown procedure (delete `jobs.db`) is documented before retry columns land.
- Phase 4/5: CI principal over-privilege risk (OWASP CICD-SEC-5) — `ci` RBAC role must restrict `signatures:write` before any CI/CD documentation is written. Address in Phase 4.
- Phase 5: Verification key TOCTOU gap — nodes fetch Ed25519 public key without pinning. Decide approach (hash in JOIN_TOKEN vs PEM embed) before Phase 4 CI/CD docs.

## Session Continuity

Last session: 2026-03-04
Stopped at: Roadmap creation complete — ROADMAP.md, STATE.md, REQUIREMENTS.md traceability written
Resume file: None
