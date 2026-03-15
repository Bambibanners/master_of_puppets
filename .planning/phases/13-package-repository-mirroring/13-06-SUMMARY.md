---
phase: 13-package-repository-mirroring
plan: "06"
subsystem: smelter-registry
tags: [gap-closure, db-schema, mirror-service, foundry-service, api-endpoints]
dependency_graph:
  requires: [13-01, 13-03]
  provides: [mirror_log-field, is_active-field, mirror-config-api, unconditional-fail-fast, soft-purge-delete, extension-based-upload]
  affects: [foundry_service.py, mirror_service.py, main.py, approved_ingredients-table]
tech_stack:
  added: []
  patterns: [soft-delete, log-capture, unconditional-fail-fast, extension-based-routing, config-db-upsert]
key_files:
  created: []
  modified:
    - puppeteer/agent_service/db.py
    - puppeteer/agent_service/models.py
    - puppeteer/migration_v29.sql
    - puppeteer/agent_service/services/mirror_service.py
    - puppeteer/agent_service/services/foundry_service.py
    - puppeteer/agent_service/main.py
decisions:
  - "Plan verification assertion for enforcement_mode check was overly strict (would have required removing enforcement_mode from unapproved-ingredients check); actual mirror fail-fast block verified clean of enforcement_mode gating"
  - "migration_v29.sql grep returns 5 for IF NOT EXISTS (comment line included) not 4 as plan says; content is correct with 4 ALTER TABLE IF NOT EXISTS statements"
metrics:
  duration: "4 minutes"
  completed_date: "2026-03-15"
  tasks_completed: 2
  files_modified: 6
---

# Phase 13 Plan 06: Backend Gap Closure (mirror_log, is_active, mirror-config, fail-fast) Summary

Closed all 6 backend gaps found in VERIFICATION.md: added the two missing DB/model fields (mirror_log, is_active), rewrote migration_v29.sql with proper IF NOT EXISTS guards on all four columns, wired subprocess log capture into MirrorService, made the foundry fail-fast unconditional with an is_active filter, rewrote the delete endpoint as soft-purge, fixed upload routing to use file extension, and added the missing mirror-config GET/PUT endpoints.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add mirror_log and is_active to DB model, Pydantic response, migration SQL | 4ce4743 | db.py, models.py, migration_v29.sql |
| 2 | Wire log capture, fix fail-fast, soft-purge delete, upload routing, mirror-config | f8f50d4 | mirror_service.py, foundry_service.py, main.py, models.py |

## Changes Made

### Task 1: DB Schema + Migration

**puppeteer/agent_service/db.py**
- Added `mirror_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)` to `ApprovedIngredient`
- Added `is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")` to `ApprovedIngredient`
- Column order: mirror_status, mirror_path, mirror_log, is_active, created_at, updated_at

**puppeteer/agent_service/models.py**
- Added `mirror_log: Optional[str] = None` to `ApprovedIngredientResponse`
- Added `is_active: bool = True` to `ApprovedIngredientResponse`

**puppeteer/migration_v29.sql**
- Rewrote from 2-column to 4-column with IF NOT EXISTS guards on all four columns

### Task 2: Services + API Endpoints

**puppeteer/agent_service/services/mirror_service.py**
- `_mirror_pypi`: set `ingredient.mirror_log = f"[stdout]\n{process.stdout}\n[stderr]\n{process.stderr}"` before returncode check
- `mirror_ingredient` exception handler: add `if not ingredient.mirror_log: ingredient.mirror_log = str(e)`

**puppeteer/agent_service/services/foundry_service.py**
- Mirror fail-fast WHERE clause: added `ApprovedIngredient.is_active == True`
- Mirror fail-fast conditional: replaced `if enforcement_mode == "STRICT": raise ...` with unconditional `raise HTTPException(403, ...)`
- Removed `else: tmpl.is_compliant = False` branch from mirror check

**puppeteer/agent_service/main.py**
- `DELETE /api/smelter/ingredients/{id}`: replaced hard-delete via `SmelterService.delete_ingredient()` with soft-purge `ing.is_active = False`
- Upload endpoint: changed `target_dir` routing from `os_family` to `file.filename.endswith(".deb")`
- Added `GET /api/admin/mirror-config`: reads PYPI_MIRROR_URL and APT_MIRROR_URL from Config DB with env var fallback
- Added `PUT /api/admin/mirror-config`: upserts both Config DB keys and audits the action
- Added `MirrorConfigUpdate` to models import block

**puppeteer/agent_service/models.py**
- Added `MirrorConfigUpdate` Pydantic model with `pypi_mirror_url: Optional[str]` and `apt_mirror_url: Optional[str]`

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written with one noted plan assertion bug.

### Plan Assertion Note (Non-Breaking)

The Task 2 verify script's assertion `'enforcement_mode' not in fs.split('is_active == True')[0].split('mirror_status')[-1]` is incorrectly formulated — it would require removing `enforcement_mode` from the unapproved-ingredients check above the mirror fail-fast, which is a separate feature. The actual requirement (mirror fail-fast raises unconditionally) is satisfied. Verified directly that the mirror fail-fast block contains no `enforcement_mode` reference.

## Self-Check

Files exist:
- puppeteer/agent_service/db.py — has mirror_log, is_active columns
- puppeteer/agent_service/models.py — has mirror_log, is_active, MirrorConfigUpdate
- puppeteer/migration_v29.sql — has 4 ALTER TABLE IF NOT EXISTS statements
- puppeteer/agent_service/services/mirror_service.py — has mirror_log capture
- puppeteer/agent_service/services/foundry_service.py — has is_active filter, unconditional raise
- puppeteer/agent_service/main.py — has soft-purge delete, .deb routing, mirror-config endpoints

Commits exist:
- 4ce4743 feat(13-06): add mirror_log and is_active
- f8f50d4 feat(13-06): wire log capture, fix fail-fast, soft-purge delete, upload routing, mirror-config endpoints
