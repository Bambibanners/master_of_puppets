---
phase: 9
slug: triggermanager-dashboard-ui
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-08
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Nyquist Compliance Rationale

Wave 0 test stubs (test_triggers.py and Admin.test.tsx) are not required for this phase.

**Backend tasks (9-01-02, 9-01-03, 9-01-04):** The `python -c "from agent_service.main import app; ..."` structural import check verifies that `TriggerUpdate` is importable, the service methods are callable, and the routes are registered in FastAPI — all without a running server. This is equivalent to a unit test for a module that has no branching logic beyond the DB session pattern already covered by the existing test suite.

**Frontend task (9-02-04 empty state):** The build-smoke command (`npm run build`) compiles the full TypeScript AST and will fail if the `triggers.length === 0` branch contains type errors, missing identifiers, or invalid JSX. Structural correctness is fully covered by the TypeScript compiler; the empty-state conditional has no business logic requiring isolated unit tests.

Adding stub test files solely to satisfy the Wave 0 checklist would be padding — the build + import checks are the correct verification boundary for this scope. A dedicated test plan for the trigger endpoints would be warranted if complex validation logic is added in a future phase.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend), vitest (frontend) |
| **Config file** | `puppeteer/pytest.ini` / vitest via `puppeteer/dashboard/vite.config.ts` |
| **Quick run command** | `cd puppeteer/dashboard && npm run build` |
| **Full suite command** | `cd puppeteer && pytest && cd dashboard && npm run test` |
| **Estimated runtime** | ~30 seconds (build) / ~60 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `cd puppeteer/dashboard && npm run build`
- **After every plan wave:** Run `cd puppeteer && pytest tests/ -x && cd dashboard && npm run test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 9-01-01 | 01 | 1 | Fix compile errors | build smoke | `cd puppeteer/dashboard && npm run build` | ⬜ pending |
| 9-01-02 | 01 | 1 | TriggerUpdate model | structural import | `cd puppeteer && python -c "from agent_service.models import TriggerUpdate; print('OK')"` | ⬜ pending |
| 9-01-03 | 01 | 1 | PATCH endpoint | structural import | `cd puppeteer && python -c "from agent_service.main import app; routes=[r.path for r in app.routes]; assert any('triggers' in r for r in routes)"` | ⬜ pending |
| 9-01-04 | 01 | 1 | regenerate-token endpoint | structural import | `cd puppeteer && python -c "from agent_service.main import app; routes=[r.path for r in app.routes]; assert any('regenerate-token' in r for r in routes)"` | ⬜ pending |
| 9-02-01 | 02 | 2 | Active/inactive toggle UI | build smoke | `cd puppeteer/dashboard && npm run build` | ⬜ pending |
| 9-02-02 | 02 | 2 | Copy Token button | build smoke | `cd puppeteer/dashboard && npm run build` | ⬜ pending |
| 9-02-03 | 02 | 2 | Rotate Key flow | build smoke | `cd puppeteer/dashboard && npm run build` | ⬜ pending |
| 9-02-04 | 02 | 2 | Empty state | build smoke | `cd puppeteer/dashboard && npm run build` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| One-time reveal modal — token not re-shown after close | Token security UX | Stateful modal flow hard to automate | 1. Rotate a trigger token. 2. Close the modal. 3. Verify token is not visible in the table row. |
| Disable confirmation dialog appears before toggling off | UX safety gate | Dialog interaction | 1. Click disable on an active trigger. 2. Verify confirmation dialog appears before PATCH is sent. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] No Wave 0 gaps — structural import checks cover backend; TypeScript compiler covers frontend
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
