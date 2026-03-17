---
phase: 24-extended-feature-guides-security
plan: "04"
subsystem: docs
tags: [mkdocs, security, mtls, pki, tls, certificates, documentation]

# Dependency graph
requires:
  - phase: 24-extended-feature-guides-security
    provides: stub files for all security section pages (created in plan 24-01)
provides:
  - Security Overview page with defence-in-depth Mermaid diagram and Compromise Scenarios table
  - mTLS & Certificates guide: PKI background, Root CA, enrollment, revocation, cert rotation
affects:
  - 24-05 (remaining security guides build on patterns established here)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PKI term define-on-first-use via info admonition before first procedure"
    - "Danger admonition at point-of-no-return in multi-step procedures"
    - "Prerequisites checklist (Markdown task list) before irreversible procedures"
    - "Compromise Scenarios table: Scenario / What attacker gains / Controls that limit damage"

key-files:
  created: []
  modified:
    - docs/docs/security/index.md
    - docs/docs/security/mtls.md

key-decisions:
  - "3 danger admonitions in mtls.md: Root CA key protection, revocation permanence, and point-of-no-return before old cert revoke"
  - "Prerequisites checklist uses Markdown task list syntax so operators can mentally check off before executing"

patterns-established:
  - "Pattern: PKI background box (info admonition) before any procedure that requires PKI knowledge"
  - "Pattern: Compromise Scenarios table with 3-column structure reusable in other security pages"

requirements-completed:
  - SECU-01

# Metrics
duration: 3min
completed: 2026-03-17
---

# Phase 24 Plan 04: Security Overview and mTLS Guide Summary

**Security Overview page with defence-in-depth Mermaid diagram plus complete mTLS guide covering Root CA (RSA 4096/10yr), node cert enrollment (825 days), CRL (7 days), revocation, and 7-step rotation procedure with prerequisites checklist and point-of-no-return danger admonition.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-17T13:51:48Z
- **Completed:** 2026-03-17T13:54:48Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Security Overview page: defence-in-depth model with Mermaid diagram, "How Controls Fit Together" narrative, Compromise Scenarios table (4 rows), links to all 4 sub-guides
- mTLS guide: PKI terminology background box defining CA, CSR, CRL, enrollment, serial number on first use
- mTLS guide: Root CA parameters (RSA 4096, 10yr/3650 days), secrets/ca/ paths, danger admonition for key protection
- mTLS guide: JOIN_TOKEN explanation, enrollment flow (6 steps), 825-day cert validity
- mTLS guide: Revocation procedure, CRL (7-day interval), permanence danger admonition
- mTLS guide: Cert rotation — prerequisites checklist, 7-step procedure, point-of-no-return danger admonition at step 6
- mkdocs build clean (pre-existing openapi.json warning is unrelated to this plan's changes)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write security/index.md — Security Overview** - `4464db9` (feat)
2. **Task 2: Write security/mtls.md — mTLS and Certificates guide** - `87b91bd` (feat)

**Plan metadata:** `1f0fdeb` (docs: complete plan)

## Files Created/Modified

- `docs/docs/security/index.md` - Security Overview: defence-in-depth model, Mermaid diagram, Compromise Scenarios table, links to all 4 security sub-guides
- `docs/docs/security/mtls.md` - Complete mTLS guide: PKI terms, Root CA, JOIN_TOKEN, enrollment, revocation, cert rotation with prereq checklist

## Decisions Made

- 3 danger admonitions placed in mtls.md: Root CA key protection, revocation permanence, and point-of-no-return at step 6 of rotation — each targets an irreversible action
- Prerequisites checklist uses Markdown task list syntax (`- [ ]`) so operators can visually check off items

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — documentation only, no external service configuration required.

## Next Phase Readiness

- Security section overview and mTLS guide complete; remaining guides (rbac-hardening, audit-log, air-gap) can proceed
- Patterns established (PKI background box, Compromise Scenarios table, prerequisites checklist, danger-at-point-of-no-return) should be reused in subsequent security guides for consistency

---
*Phase: 24-extended-feature-guides-security*
*Completed: 2026-03-17*
