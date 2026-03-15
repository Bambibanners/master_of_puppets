---
phase: 19-dashboard-staging-view-and-governance-doc
plan: "03"
subsystem: docs
tags: [oidc, oauth2, device-flow, ed25519, governance, documentation]

# Dependency graph
requires:
  - phase: 17-backend-oauth-device-flow-and-job-staging
    provides: OAuth Device Flow endpoints and job staging backend
  - phase: 18-cli-mop-push-implementation
    provides: mop-push CLI that drives the staging workflow
provides:
  - OIDC integration architecture document with device flow contract and v2 roadmap
  - UserGuide staging workflow section covering lifecycle statuses and publish steps
affects:
  - future OIDC provider integration work
  - onboarding documentation for operators using mop-push CLI

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Dual-factor integrity model (JWT identity + Ed25519 payload proof)
    - Device flow contract documented as API reference for CLI and OIDC migration

key-files:
  created:
    - docs/architecture/OIDC_INTEGRATION.md
  modified:
    - docs/UserGuide.md

key-decisions:
  - "GOV-CLI-02: OIDC v2 doc placed in Phase 19 — architecture document for future device flow contract, co-located with dashboard delivery that completes the end-to-end UX"

patterns-established:
  - "Dual-factor integrity: all job push endpoints require both JWT (identity) and Ed25519 signature (payload proof) — compromised OIDC session cannot publish unauthorized scripts without the operator's local private key"

requirements-completed: []

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 19 Plan 03: Governance Documentation Summary

**OIDC integration architecture and job staging lifecycle documentation for operator governance of the mop-push → Dashboard → publish workflow**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-15T15:31:53Z
- **Completed:** 2026-03-15T15:36:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created `docs/architecture/OIDC_INTEGRATION.md` documenting the current OAuth Device Flow contract (RFC 8628) and the v2 roadmap for external OIDC providers
- Documented the dual-factor integrity model: JWT identity layer + Ed25519 payload layer, explaining why compromising one layer is insufficient for unauthorized publication
- Added Section 6 to `docs/UserGuide.md` covering all four job lifecycle statuses (DRAFT, ACTIVE, DEPRECATED, REVOKED) and the 4-step staging workflow

## Task Commits

Each task was committed atomically:

1. **Task 1: Create OIDC_INTEGRATION.md** - `57de7cd` (docs)
2. **Task 2: Update UserGuide.md staging section** - `5e793f5` (docs)

**Plan metadata:** (created below in final commit)

## Files Created/Modified
- `docs/architecture/OIDC_INTEGRATION.md` - OAuth Device Flow contract, OIDC v2 roadmap, dual-factor integrity model, API contract specification
- `docs/UserGuide.md` - Section 6 added: job staging workflow, lifecycle status definitions, governance rules

## Decisions Made
- None beyond what was already recorded in STATE.md for this phase — both documents follow the architecture already implemented in Phase 17/18.

## Deviations from Plan

None — plan executed exactly as written. Both documents were already present in the working tree (work done in a prior session); this plan execution committed them with proper atomic commits.

## Issues Encountered
None. Documents were already authored in the working tree before this execution session.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- All three documentation/UI plans for Phase 19 (01, 02, 03) are now committed with SUMMARY.md files
- Phase 19 Plan 04 (E2E walkthrough: push DRAFT via CLI → verify in Staging tab → publish → verify in Active tab) is the remaining work
- The import blocker in `main.py` (missing `ImageBOMResponse` and `PackageIndexResponse` imports) must be resolved before E2E tests can run

---
*Phase: 19-dashboard-staging-view-and-governance-doc*
*Completed: 2026-03-15*
