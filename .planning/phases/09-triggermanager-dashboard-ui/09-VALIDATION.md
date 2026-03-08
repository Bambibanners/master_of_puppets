---
phase: 9
slug: triggermanager-dashboard-ui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-08
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

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

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 9-01-01 | 01 | 1 | Fix compile errors | build smoke | `cd puppeteer/dashboard && npm run build` | N/A | ⬜ pending |
| 9-01-02 | 01 | 1 | TriggerUpdate model | unit | `cd puppeteer && pytest tests/ -k trigger -x` | ❌ W0 | ⬜ pending |
| 9-01-03 | 01 | 1 | PATCH endpoint | integration | `cd puppeteer && pytest tests/ -k trigger -x` | ❌ W0 | ⬜ pending |
| 9-01-04 | 01 | 1 | regenerate-token endpoint | integration | `cd puppeteer && pytest tests/ -k trigger -x` | ❌ W0 | ⬜ pending |
| 9-02-01 | 02 | 2 | Active/inactive toggle UI | build smoke | `cd puppeteer/dashboard && npm run build` | N/A | ⬜ pending |
| 9-02-02 | 02 | 2 | Copy Token button | build smoke | `cd puppeteer/dashboard && npm run build` | N/A | ⬜ pending |
| 9-02-03 | 02 | 2 | Rotate Key flow | build smoke | `cd puppeteer/dashboard && npm run build` | N/A | ⬜ pending |
| 9-02-04 | 02 | 2 | Empty state | unit | `cd puppeteer/dashboard && npx vitest run src/views/__tests__/Admin.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `puppeteer/tests/test_triggers.py` — stubs for PATCH toggle and regenerate-token endpoints
- [ ] `puppeteer/dashboard/src/views/__tests__/Admin.test.tsx` — smoke render test for TriggerManager empty state

*Wave 0 creates test stubs before the feature code is written, ensuring test-first validation.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| One-time reveal modal — token not re-shown after close | Token security UX | Stateful modal flow hard to automate | 1. Rotate a trigger token. 2. Close the modal. 3. Verify token is not visible in the table row. |
| Disable confirmation dialog appears before toggling off | UX safety gate | Dialog interaction | 1. Click disable on an active trigger. 2. Verify confirmation dialog appears before PATCH is sent. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
