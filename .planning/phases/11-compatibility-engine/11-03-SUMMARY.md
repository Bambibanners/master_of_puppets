---
phase: 11-compatibility-engine
plan: "03"
subsystem: api
tags: [pydantic, validation, blueprints, capability-matrix, os-compatibility, foundry]

# Dependency graph
requires:
  - phase: 11-02
    provides: CapabilityMatrix with is_active, runtime_dependencies, base_os_family columns + CRUD endpoints
provides:
  - BlueprintCreate model with os_family (required for RUNTIME) + confirmed_deps (dep-confirmation resubmit)
  - BlueprintResponse model with os_family field
  - POST /api/blueprints two-pass OS + runtime dep validation gate
  - create_blueprint writes os_family to DB column
  - list_blueprints includes os_family in response
affects: [11-04, 11-05, 11-06, foundry-service, blueprint-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-pass blueprint validation: Pass 1 hard rejects OS mismatches (422 + offending_tools), Pass 2 soft rejects missing deps (422 + deps_to_confirm) with confirmed_deps resubmit flow"
    - "pydantic model_validator(mode='after') for cross-field validation (RUNTIME requires os_family)"
    - "field_validator normalizes os_family to uppercase before cross-field check"
    - "getattr with fallback for backwards-compatible DB column access in foundry_service"

key-files:
  created: []
  modified:
    - puppeteer/agent_service/models.py
    - puppeteer/agent_service/main.py
    - puppeteer/agent_service/services/foundry_service.py

key-decisions:
  - "RUNTIME blueprints: os_family required via model_validator (422 from Pydantic before hitting DB); NETWORK blueprints bypass all validation"
  - "Pass 1 is a hard reject (incompatible OS means the image literally cannot be built); Pass 2 is a soft reject (deps can be confirmed and auto-added)"
  - "confirmed_deps auto-adds entries with version='latest' to the tool list before saving — caller doesn't have to rebuild the definition manually"
  - "foundry_service uses rt_bp.os_family as primary source with derived string as fallback — preserves backwards compat for blueprints created before Phase 11"

patterns-established:
  - "Two-pass validation pattern: source-of-truth validation → derived validation with user escape hatch"
  - "Auto-add confirmed items to persisted definition before save (no extra round-trip required)"

requirements-completed: [COMP-03]

# Metrics
duration: 3min
completed: 2026-03-11
---

# Phase 11 Plan 03: Blueprint OS Compatibility Validation Summary

**Two-pass OS + runtime dependency gate on POST /api/blueprints — RUNTIME blueprints are rejected (422) if tools are incompatible with declared os_family or have unconfirmed runtime deps; confirmed_deps are auto-added to the saved definition**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-11T10:22:47Z
- **Completed:** 2026-03-11T10:25:50Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- `BlueprintCreate` now requires `os_family` for RUNTIME type (Pydantic model_validator raises 422 before any DB query)
- `confirmed_deps` field added to `BlueprintCreate` for the dep-confirmation resubmit flow
- `BlueprintResponse` and `list_blueprints` now include `os_family`
- `create_blueprint` route enforces two-pass validation: Pass 1 checks CapabilityMatrix for OS-tool compatibility (hard 422 with `offending_tools`); Pass 2 checks runtime deps (soft 422 with `deps_to_confirm`)
- `foundry_service.py` now uses `rt_bp.os_family` as the primary source for os_family (with derived fallback)
- All COMP-03 tests pass (4 passed, 1 correctly skipped)

## Task Commits

Each task was committed atomically:

1. **Task 1: Update BlueprintCreate + BlueprintResponse models** - `057aec7` (feat)
2. **Task 2: Two-pass validation in create_blueprint route** - `43242cb` (feat)

## Files Created/Modified
- `puppeteer/agent_service/models.py` - Added os_family + confirmed_deps to BlueprintCreate; added os_family to BlueprintResponse; added model_validator import
- `puppeteer/agent_service/main.py` - create_blueprint with two-pass validation; list_blueprints returns os_family; status_code=201
- `puppeteer/agent_service/services/foundry_service.py` - Use rt_bp.os_family as primary source with derived string as fallback

## Decisions Made
- RUNTIME blueprints require os_family via Pydantic model_validator — raises ValueError before hitting the DB, giving a clean 422 from the model layer rather than from a DB null constraint
- Pass 1 is a hard reject: if the tool has no CapabilityMatrix entry for the declared OS, the image literally cannot be built — no escape hatch needed
- Pass 2 is a soft reject: missing runtime deps can be confirmed by the caller and auto-added to the definition before saving — no extra client round-trip required
- foundry_service uses rt_bp.os_family as primary source with derived string as fallback to maintain backwards compatibility with blueprints created before Phase 11

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Test isolation across test_alert_system.py:** `test_alert_system.py` replaces `sys.modules['agent_service.main']` with a `MagicMock` at module load time. When it runs before `test_compatibility_engine.py`, the real module is never loaded, causing `inspect.getsource()` to fail. This is a pre-existing issue predating Plan 03. All COMP-03 tests pass when run in isolation (as the plan verification specifies). Logged to deferred-items.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- COMP-03 gate is complete — blueprint creation now enforces OS + dep compatibility
- Plan 04 (matrix admin UI) can now surface os_family data from blueprints
- Plan 05 (wizard filtering) can use the validated os_family stored in the blueprints table
- Blueprints created before Phase 11 will have os_family=NULL — foundry_service fallback handles these gracefully

## Self-Check: PASSED

All files found and all commits verified.

---
*Phase: 11-compatibility-engine*
*Completed: 2026-03-11*
