---
phase: 34-ce-baseline-fixes
verified: 2026-03-19T20:45:00Z
status: gaps_found
score: 7/8 must-haves verified
re_verification: false
gaps:
  - truth: "pytest -m 'not ee_only' runs to completion with zero failures and zero attribute errors on User.role"
    status: partial
    reason: "Running the full two-directory target (agent_service/tests/ + puppeteer/tests/) causes collection errors in puppeteer/tests/ — 8 EE integration test files there import missing CE symbols (TriggerUpdate, Blueprint, etc.) and have no ee_only markers, halting collection before any tests run. Running agent_service/tests/ alone yields 27 passed + 2 pre-existing failures (test_get_job_stats, test_flight_recorder_on_failure in test_sprint3.py — 422 vs 200 response code mismatch). The plan's GAP-03 deliverable targeted agent_service/tests/ only; puppeteer/tests/ was explicitly noted as deferred follow-up in the Plan 02 SUMMARY. However the phase goal states 'pytest suite passes clean' without qualification, so this gap is recorded."
    artifacts:
      - path: ".worktrees/axiom-split/puppeteer/tests/"
        issue: "8 EE integration test files lack @pytest.mark.ee_only — collection fails when this directory is included in pytest run"
      - path: ".worktrees/axiom-split/puppeteer/agent_service/tests/test_sprint3.py"
        issue: "2 pre-existing test failures: test_get_job_stats and test_flight_recorder_on_failure (422 vs 200 response code — pre-dates Phase 34, documented in Plan 02 SUMMARY)"
    missing:
      - "Add @pytest.mark.ee_only to all EE integration tests in puppeteer/tests/ (or exclude that directory from the CE test run via pytest configuration)"
      - "Fix or skip test_sprint3.py::test_get_job_stats and test_flight_recorder_on_failure (pre-existing, not introduced by Phase 34)"
---

# Phase 34: CE Baseline Fixes — Verification Report

**Phase Goal:** The CE install behaves correctly — all EE paths return 402, the pytest suite passes clean with zero EE-attribute errors, and job dispatch works without dead-field crashes

**Verified:** 2026-03-19T20:45:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every EE route returns HTTP 402 on a CE-only install (not 404) | VERIFIED | `_mount_ce_stubs()` defined and called in both CE paths (`else` + `except`); 6 stub routers mounted via `app.include_router()`; all routes return `JSONResponse(status_code=402)` |
| 2 | `load_ee_plugins()` uses `importlib.metadata`, not `pkg_resources` | VERIFIED | `from importlib.metadata import entry_points; plugins = list(entry_points(group="axiom.ee"))` — zero `pkg_resources` references remain in file |
| 3 | Stub routers mounted in both the no-plugin and exception paths | VERIFIED | Lines 62 and 65 of `ee/__init__.py` both call `_mount_ce_stubs(app)` |
| 4 | `pytest -m 'not ee_only'` runs to completion with zero failures | PARTIAL | `agent_service/tests/` alone: 27 passed, 4 skipped (ee_only), 2 pre-existing failures in test_sprint3.py; `puppeteer/tests/` causes 8 collection ERRORs (EE files without ee_only markers, noted as deferred in Plan 02 SUMMARY) |
| 5 | EE-only placeholder tests are automatically skipped when axiom-ee is not installed | VERIFIED | All 4 placeholder files exist with `@pytest.mark.ee_only`; `pytest_collection_modifyitems` hook present in conftest.py; actual pytest run shows `4 deselected` |
| 6 | No `PytestUnknownMarkWarning` for the ee_only marker | VERIFIED | Marker registered in root `pyproject.toml` under `[tool.pytest.ini_options] markers`; no warning observed in test run |
| 7 | `bootstrap_admin.py` creates a User without the `role=` keyword argument | VERIFIED | Lines 20-23: `User(username="admin", password_hash=get_password_hash(admin_pwd))` — no `role=` kwarg |
| 8 | Job dispatch completes without AttributeError from NodeConfig fields | VERIFIED | `NodeConfig` class fully deleted from `models.py`; zero matches for `NodeConfig` across all `.py` files in `puppeteer/` and `puppets/`; `PollResponse` simplified to `job + env_tag`; `node.py` reads `job_data.get("env_tag")` directly |
| 9 | `GET /api/features` returns all feature flags as false on a CE-only install | VERIFIED | Route at `main.py:820`; CE path (`ctx is None`) returns hardcoded dict with all 8 flags `False`; `app.state.ee = load_ee_plugins(app, engine)` confirms EE context populated at startup |
| 10 | `node.py` reads `env_tag` from flat job_data dict, not nested config dict | VERIFIED | `node.py:770`: `pushed_tag = job_data.get("env_tag")` — no `config = job_data.get("config", {})` block remains |

**Score:** 9/10 truths verified (1 partial)

---

### Required Artifacts

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `.worktrees/axiom-split/puppeteer/agent_service/ee/__init__.py` | `_mount_ce_stubs()` helper + `importlib.metadata` entry point lookup | VERIFIED | 68 lines; `_mount_ce_stubs` defined line 26, called lines 62 and 65; `importlib.metadata.entry_points` used line 53 |
| `.worktrees/axiom-split/puppeteer/agent_service/ee/interfaces/auth_ext.py` | Complete user sub-route stubs including reset-password and force-password-change | VERIFIED | 86 lines; `reset-password` at line 72, `force-password-change` at line 75, both returning `_EE_RESPONSE` (status 402) |
| `.worktrees/axiom-split/pyproject.toml` | `ee_only` marker registration | VERIFIED | `markers = ["ee_only: marks tests that require the axiom-ee package (skipped in CE)"]` present under `[tool.pytest.ini_options]` |
| `.worktrees/axiom-split/puppeteer/agent_service/tests/conftest.py` | `pytest_collection_modifyitems` hook skipping ee_only tests | VERIFIED | Hook at line 47; uses `importlib.metadata.PackageNotFoundError` for EE presence detection |
| `.worktrees/axiom-split/puppeteer/agent_service/tests/test_lifecycle_enforcement.py` | ee_only placeholder test | VERIFIED | Single `@pytest.mark.ee_only` test with `pass` body |
| `.worktrees/axiom-split/puppeteer/agent_service/tests/test_foundry_mirror.py` | ee_only placeholder test | VERIFIED | Single `@pytest.mark.ee_only` test with `pass` body |
| `.worktrees/axiom-split/puppeteer/agent_service/tests/test_smelter.py` | ee_only placeholder test | VERIFIED | Single `@pytest.mark.ee_only` test with `pass` body |
| `.worktrees/axiom-split/puppeteer/agent_service/tests/test_staging.py` | ee_only placeholder test | VERIFIED | Single `@pytest.mark.ee_only` test with `pass` body |
| `.worktrees/axiom-split/puppeteer/bootstrap_admin.py` | User constructor without role= kwarg | VERIFIED | Lines 20-23; `User(username="admin", password_hash=...)` only |
| `.worktrees/axiom-split/puppeteer/agent_service/models.py` | `PollResponse` with `env_tag` field; `NodeConfig` class deleted | VERIFIED | `NodeConfig` absent (zero grep hits); `PollResponse` at lines 105-107: `job + env_tag` only |
| `.worktrees/axiom-split/puppeteer/agent_service/services/job_service.py` | `pull_work()` returning `PollResponse` without NodeConfig construction | VERIFIED | All return sites use `PollResponse(job=None)` or `PollResponse(job=work_resp, env_tag=current_env_tag)` — zero NodeConfig constructions |
| `.worktrees/axiom-split/puppets/environment_service/node.py` | Poll response consumer reading `env_tag` from flat dict | VERIFIED | Line 770: `pushed_tag = job_data.get("env_tag")` — no nested config dict access |
| `.worktrees/axiom-split/puppeteer/agent_service/main.py` | `GET /api/features` route returning all-false dict when `app.state.ee is None` | VERIFIED | Lines 820-826: CE path returns `{"audit": False, "foundry": False, ...}` for all 8 flags |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `ee/__init__.py` else branch | `_mount_ce_stubs(app)` | CE no-plugin path | WIRED | Line 62: `_mount_ce_stubs(app)` after `logger.info("No EE plugins found...")` |
| `ee/__init__.py` except handler | `_mount_ce_stubs(app)` | CE exception fallback path | WIRED | Line 65: `_mount_ce_stubs(app)` after `logger.warning(...)` |
| `_mount_ce_stubs()` | All 6 stub routers | `app.include_router()` | WIRED | Lines 33-38: 6 `app.include_router()` calls (foundry, audit, webhooks, triggers, auth_ext, smelter) |
| `auth_ext_stub_router` | `reset-password` + `force-password-change` | `@router.patch()` stubs | WIRED | Lines 72-76 in `auth_ext.py`; both return `_EE_RESPONSE` (402) |
| `job_service.pull_work()` | `PollResponse(job=..., env_tag=...)` | `PollResponse` constructor | WIRED | 4 return sites in `job_service.py` all use simplified `PollResponse` |
| `node.py` poll loop | `env_tag` from `job_data` | `job_data.get("env_tag")` | WIRED | Line 770: direct flat dict access, no config sub-dict nesting |
| `main.py` lifespan | `load_ee_plugins(app, engine)` | `app.state.ee` assignment | WIRED | Line 71: `app.state.ee = load_ee_plugins(app, engine)` |
| `GET /api/features` | `app.state.ee` | `getattr(request.app.state, "ee", None)` | WIRED | Lines 822-826: None check returns all-false dict |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| GAP-01 | Plan 01 | CE mode returns 402 (not 404) for all EE routes — all 7 stub routers mounted in `load_ee_plugins()` | SATISFIED | `_mount_ce_stubs()` mounts 6 HTTP routers (rbac + resource_limits are Python interface stubs, not HTTP routers; the "7" in REQUIREMENTS.md conflates the two types) |
| GAP-02 | Plan 01 | `load_ee_plugins()` uses `importlib.metadata.entry_points()` instead of deprecated `pkg_resources` | SATISFIED | `from importlib.metadata import entry_points; list(entry_points(group="axiom.ee"))` at lines 52-53 |
| GAP-03 | Plan 02 | EE-only test files isolated with `@pytest.mark.ee_only` marker + conftest skip logic | SATISFIED (scoped) | 4 placeholder files in `agent_service/tests/` have `ee_only` marker and are auto-skipped; `puppeteer/tests/` EE integration files still fail on collection — documented as deferred in Plan 02 SUMMARY |
| GAP-04 | Plan 02 | `User.role` attribute references removed — CE pytest suite passes cleanly | SATISFIED | All 5 files cleaned: `bootstrap_admin.py`, `test_bootstrap_admin.py`, `test_db.py`, `test_scheduler_service.py`, `test_signature_service.py`; only comment reference remains at `test_bootstrap_admin.py:34` |
| GAP-05 | Plan 03 | `NodeConfig` Pydantic model stripped of EE-only fields | SATISFIED (exceeded) | `NodeConfig` fully deleted (not just stripped) — zero references anywhere in `puppeteer/` or `puppets/`; `PollResponse` simplified; `NodeUpdateRequest` added as CE-safe replacement for `PATCH /nodes/{id}` |
| GAP-06 | Plan 03 | `job_service.py` EE field workarounds removed and replaced with CE-appropriate defaults | SATISFIED | All 3 `NodeConfig(...)` construction sites removed; all `PollResponse(... config=node_config)` replaced with flat `PollResponse(job=..., env_tag=...)`; `node.py` poll consumer updated |

**No orphaned requirements** — all 6 GAP requirements for Phase 34 appear in plan frontmatter.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `puppeteer/tests/test_lifecycle_enforcement.py` | 1 | EE integration test file — no `ee_only` marker; imports `puppeteer.agent_service.*` prefix causing `ModuleNotFoundError` on collection | Warning | Collection of `puppeteer/tests/` directory fails entirely when this file is included (8 files affected) |
| `puppeteer/agent_service/tests/test_sprint3.py` | ~35, ~51 | 2 pre-existing test failures: 422 vs 200 response assertions | Warning | Documented as pre-existing in Plan 02 SUMMARY; not introduced by Phase 34 |

Note: Both anti-patterns are pre-existing issues explicitly documented in Plan 02 SUMMARY as deferred, not caused by Phase 34 changes.

---

### Human Verification Required

None — all observable truths can be verified programmatically.

---

### Gaps Summary

**One gap** blocks the phase goal's "pytest suite passes clean" claim:

The plan's GAP-03 work (Plan 02) correctly isolated the 4 new placeholder test files in `puppeteer/agent_service/tests/` with `ee_only` markers. However, the `puppeteer/tests/` directory contains 8 pre-existing EE integration test files (e.g., `test_trigger_service.py`, `test_foundry_mirror.py`, `test_lifecycle_enforcement.py`) that import missing CE symbols and have no `ee_only` markers. When the full two-directory pytest invocation (`agent_service/tests/ puppeteer/tests/`) is run, collection halts with 8 errors before any tests execute.

Additionally, `test_sprint3.py` has 2 pre-existing failures (response code mismatches) that were present before Phase 34 and were documented as such.

The Plan 02 SUMMARY explicitly acknowledges: "puppeteer/tests/ EE integration files (test_foundry_mirror.py etc.) still fail with ImportError — these need ee_only markers or exclusion in a follow-up plan (not blocking Phase 35)."

**Root cause:** GAP-03's scope was scoped to creating 4 placeholder files in `agent_service/tests/`. The pre-existing `puppeteer/tests/` EE files were not included in the GAP-03 fix scope and need a follow-up plan.

**To resolve:** Either (a) add `@pytest.mark.ee_only` to all EE integration files in `puppeteer/tests/`, or (b) add a `testpaths` configuration to `pyproject.toml` that excludes `puppeteer/tests/` from the default CE run, with `puppeteer/tests/` requiring explicit opt-in.

All other phase deliverables are fully implemented and wired correctly.

---

_Verified: 2026-03-19T20:45:00Z_
_Verifier: Claude (gsd-verifier)_
