---
phase: 22-developer-documentation
plan: "03"
subsystem: docs
tags: [mkdocs, contributing, black, ruff, pyproject, documentation]

# Dependency graph
requires:
  - phase: 22-01
    provides: architecture.md nav entry and admonition/mermaid extensions in mkdocs.yml
  - phase: 22-02
    provides: setup-deployment.md nav entry in mkdocs.yml
provides:
  - Contributing guide at docs/docs/developer/contributing.md (259 lines) with PR bar checklist, pytest/npm test commands, no-Alembic migration warning, Black+Ruff code style section
  - puppeteer/pyproject.toml with Black (88-char, py312) and Ruff (E/F/I/W rules, E501 ignored, isort first-party config)
  - Complete Developer nav in mkdocs.yml (architecture, setup-deployment, contributing)
  - All legacy documentation deleted (14 root docs/ files, docs/architecture/ dir, puppeteer/docs/ dir)
affects: [future contributors, phase 23 nav restructure, any plan referencing legacy docs files]

# Tech tracking
tech-stack:
  added: [black, ruff, pyproject.toml]
  patterns: [pyproject.toml as single source of truth for Python tooling config, contributing guide with explicit PR checklist and warning admonitions for gotchas]

key-files:
  created:
    - docs/docs/developer/contributing.md
    - puppeteer/pyproject.toml
  modified:
    - docs/mkdocs.yml

key-decisions:
  - "pyproject.toml added as config file only — black/ruff not run on existing code in this phase (deferred to separate PR/commit to keep diffs reviewable)"
  - "migration_v31.sql noted as current highest migration in contributing guide — next contributor uses v32"
  - "Contributing guide points readers to both architecture.md and the API reference docs for context, establishing the docs site as the canonical reference"

patterns-established:
  - "Warning admonitions for major contributor gotchas (no-Alembic migration pattern highlighted with !!! warning)"
  - "PR checklist format in contributing guide — explicit checkbox list rather than prose"

requirements-completed: [DEVDOC-03]

# Metrics
duration: 6min
completed: 2026-03-17
---

# Phase 22 Plan 03: Contributing Guide, pyproject.toml, and Legacy Docs Cleanup Summary

**Contributing guide (259 lines) with explicit PR checklist and no-Alembic migration warning, Black+Ruff config in pyproject.toml, complete Developer nav, and 24 legacy documentation files/directories deleted.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-03-17T09:41:33Z
- **Completed:** 2026-03-17T09:46:43Z
- **Tasks:** 2 of 3 (Task 3 is checkpoint:human-verify — awaiting human sign-off on Docker build)
- **Files modified:** 27 (3 created/modified, 24 deleted)

## Accomplishments

- Contributing guide written from scratch at `docs/docs/developer/contributing.md` (259 lines): PR bar checklist, exact test commands (`cd puppeteer && pytest`, `cd puppeteer/dashboard && npm run test`), Black+Ruff code style with setup instructions, no-Alembic migration warning admonition with SQL format examples, code structure orientation, WebSocket events guide, env var reference table
- `puppeteer/pyproject.toml` created with Black (88-char, py312 target) and Ruff (E/F/I/W rules, E501 ignored, isort first-party for `agent_service`/`model_service`)
- `docs/mkdocs.yml` Developer nav completed: Architecture + Setup & Deployment + Contributing
- 14 root `docs/` legacy files deleted, `docs/architecture/` directory deleted (1 file), `puppeteer/docs/` directory deleted (9 files)
- Docker build (`docker build -f docs/Dockerfile . --no-cache`) passes — mkdocs build --strict succeeds

## Task Commits

1. **Task 1: Write contributing guide and create pyproject.toml** - `fe5623b` (feat)
2. **Task 2: Add Contributing nav entry and delete all legacy documentation files** - `504ef9e` (feat)

## Files Created/Modified

- `docs/docs/developer/contributing.md` — Contributing guide, 259 lines, 8 sections
- `puppeteer/pyproject.toml` — Black + Ruff + isort configuration (new file)
- `docs/mkdocs.yml` — Contributing nav entry added (third Developer entry)

## Files Deleted

Legacy documentation files (all outside `docs/docs/` so mkdocs build unaffected):
- `docs/architecture.md`, `docs/INSTALL.md`, `docs/deployment_guide.md`, `docs/SDK_GUIDE.md`
- `docs/UserGuide.md`, `docs/scheduling.md`, `docs/security.md`, `docs/security_signatures.md`
- `docs/ssl_guide.md`, `docs/compatibility.md`, `docs/REMOTE_DEPLOYMENT.md`
- `docs/third_party_audit_report.md`, `docs/WEBHOOKS.md`, `docs/API_REFERENCE.md`
- `docs/architecture/OIDC_INTEGRATION.md` (entire `docs/architecture/` dir)
- `puppeteer/docs/` directory: architecture.md, UserGuide.md, compatibility.md, deployment_guide.md, scheduling.md, security.md, security_signatures.md, ssl_guide.md, third_party_audit_report.md

## Decisions Made

- pyproject.toml added as config file only — Black and Ruff not run against the existing codebase in this phase. Style-only reformatting explicitly deferred to a separate commit/PR so diffs stay reviewable (documented as a rule in the contributing guide itself).
- Contributing guide instructs contributors to use `migration_v32.sql` as the next migration number, establishing a clear handoff point.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Test suite execution verification was complicated by the shell environment: the project's venv pytest is at `.venv/bin/pytest`, not on PATH; `test_bootstrap_admin.py` and `test_intent_scanner.py` fail with `ModuleNotFoundError` (pre-existing, environment-level, unrelated to documentation changes); `Login.test.tsx` frontend test fails with button text mismatch (pre-existing). None of these failures were introduced by this plan's changes.

## Next Phase Readiness

- All three Developer guides are now live in MkDocs: architecture, setup-deployment, contributing
- pyproject.toml establishes Black+Ruff as the codebase standard — can now apply formatting in a dedicated cleanup PR
- Legacy docs completely cleared — `docs/` root contains only Dockerfile, mkdocs.yml, nginx.conf, requirements.txt, assets/, and docs/
- Phase 23 nav restructure (if planned) starts from a clean, canonical docs structure

---
*Phase: 22-developer-documentation*
*Completed: 2026-03-17*
