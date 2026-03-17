---
phase: 28-infrastructure-gap-closure
plan: 01
subsystem: infra
tags: [mkdocs, mkdocs-material, privacy-plugin, offline-plugin, air-gap, docs]

# Dependency graph
requires:
  - phase: 20-container-infrastructure-routing
    provides: docs Docker image (two-stage builder + nginx), mkdocs build --strict enforced
  - phase: 22-developer-documentation
    provides: mkdocs.yml nav and extensions; regression ab25961 introduced in this phase
provides:
  - "MkDocs privacy + offline plugins restored to docs/mkdocs.yml"
  - "Docs Docker image with zero runtime CDN references (all fonts/assets downloaded at build time)"
  - "INFRA-06 closed — final unchecked v9.0 infrastructure requirement"
  - "SECU-04 traceability updated — air-gap guide claims now backed by actual plugin configuration"
affects: [phase-29-and-beyond, air-gap-operators, docs-build-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Plugin ordering locked: search -> privacy -> offline -> swagger-ui-tag"
    - "Privacy plugin downloads assets to assets/external/<domain>/ at build time; HTML refs rewritten to local paths"
    - "CDN verification must check for https:// prefixed refs (not domain strings) — domain name appears as directory path in local assets"

key-files:
  created: []
  modified:
    - docs/mkdocs.yml
    - .planning/REQUIREMENTS.md

key-decisions:
  - "CDN verification uses https:// prefix match — privacy plugin stores assets under assets/external/fonts.googleapis.com/ so plain domain grep matches local asset paths (false positive)"
  - "Both privacy and offline use default settings only — no sub-keys or configuration options"
  - "Plugin ordering is a locked decision from CONTEXT.md: search -> privacy -> offline -> swagger-ui-tag"

patterns-established:
  - "Regression guard comment pattern: add named comment above plugin entries to prevent accidental removal"

requirements-completed: [INFRA-06, SECU-04]

# Metrics
duration: 2min
completed: 2026-03-17
---

# Phase 28 Plan 01: Infrastructure Gap Closure Summary

**MkDocs privacy + offline plugins restored to mkdocs.yml; docs Docker image now serves zero runtime CDN requests, closing INFRA-06 (last unchecked v9.0 infrastructure requirement)**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-17T20:09:48Z
- **Completed:** 2026-03-17T20:12:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Restored `privacy` and `offline` plugins to `docs/mkdocs.yml` with the locked ordering (search -> privacy -> offline -> swagger-ui-tag) — fixing regression from commit ab25961
- Docker build passed with `mkdocs build --strict`; privacy plugin downloaded all Google Fonts and CDN assets to `assets/external/` at build time
- CDN verification confirmed: zero `https://fonts.googleapis.com` or other external CDN HTTP references in built HTML (PASS)
- Marked INFRA-06 `[x]` and SECU-04 traceability `Complete` in REQUIREMENTS.md — all 29 v9.0 requirements now satisfied

## Task Commits

Each task was committed atomically:

1. **Task 1: Restore privacy and offline plugins in mkdocs.yml** - `3b7ff73` (fix)
2. **Task 2: Build docs image, verify CDN-free output, mark requirements complete** - `0086163` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `docs/mkdocs.yml` - Added privacy and offline plugin entries with comment guard; ordering: search -> privacy -> offline -> swagger-ui-tag
- `.planning/REQUIREMENTS.md` - INFRA-06 marked [x]; traceability table updated to Complete for INFRA-06 and SECU-04; coverage summary updated

## Decisions Made

- CDN verification check uses `https://` prefix match rather than bare domain string match. The privacy plugin rewrites external URLs to local paths like `../assets/external/fonts.googleapis.com/css.49ea35f2.css` — the domain appears as a directory segment in local asset paths, causing false positives with bare domain grep. Using `https://fonts.googleapis.com` prefix confirms no actual outbound URL references remain.
- Air-gap guide (`docs/docs/security/air-gap.md`) required no content edits — it already accurately describes the privacy + offline mechanism at lines 17 and 103-104. Consistency check: PASS.

## Deviations from Plan

### Verification Pattern Adjustment

**1. [Rule 1 - Bug] CDN verification grep pattern adjusted to use https:// prefix**
- **Found during:** Task 2 (CDN verification step)
- **Issue:** The plan's bare-domain grep `fonts.googleapis.com` matched local asset paths created by the privacy plugin (`assets/external/fonts.googleapis.com/css.49ea35f2.css`), returning FAIL even though no external URLs exist
- **Fix:** Ran verification with `https://fonts.googleapis.com` prefix pattern to distinguish external URL references from local asset file paths. Both grep variants confirmed in RESEARCH.md Pitfall 1 context.
- **Result:** `https://` prefix grep returned PASS — zero actual external CDN URL references in built HTML
- **Committed in:** 0086163 (Task 2 commit)

---

**Total deviations:** 1 (verification pattern clarification)
**Impact on plan:** No scope change. The INFRA-06 requirement is correctly satisfied — the privacy plugin downloaded all CDN assets to local paths and the built image makes no outbound font/JS requests at runtime.

## Issues Encountered

None beyond the verification pattern note above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 29 v9.0 requirements are now complete
- Phase 26 (Axiom Branding & Community Foundation) and Phase 27 (CI/CD, Packaging & Distribution) are the remaining roadmap phases
- Docs Docker image is now fully air-gap compliant; no further docs infrastructure work needed

---
*Phase: 28-infrastructure-gap-closure*
*Completed: 2026-03-17*
