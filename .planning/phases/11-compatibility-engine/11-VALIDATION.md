---
phase: 11
slug: compatibility-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), vitest (frontend) |
| **Config file** | `puppeteer/pytest.ini` (or none — run from `puppeteer/` dir) |
| **Quick run command** | `cd puppeteer && pytest tests/test_compatibility_engine.py -x` |
| **Full suite command** | `cd puppeteer && pytest` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd puppeteer && pytest tests/test_compatibility_engine.py -x`
- **After every plan wave:** Run `cd puppeteer && pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 0 | COMP-01, COMP-02 | unit stub | `cd puppeteer && pytest tests/test_compatibility_engine.py -x` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | COMP-01 | unit | `cd puppeteer && pytest tests/test_compatibility_engine.py::test_matrix_has_os_family -x` | ❌ W0 | ⬜ pending |
| 11-01-03 | 01 | 1 | COMP-02 | unit | `cd puppeteer && pytest tests/test_compatibility_engine.py::test_matrix_runtime_deps -x` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | COMP-03 | unit | `cd puppeteer && pytest tests/test_compatibility_engine.py::test_blueprint_os_mismatch_rejected -x` | ❌ W0 | ⬜ pending |
| 11-02-02 | 02 | 1 | COMP-03 | unit | `cd puppeteer && pytest tests/test_compatibility_engine.py::test_blueprint_dep_confirmation_flow -x` | ❌ W0 | ⬜ pending |
| 11-03-01 | 03 | 1 | COMP-04 | unit | `cd puppeteer && pytest tests/test_compatibility_engine.py::test_matrix_os_family_filter -x` | ❌ W0 | ⬜ pending |
| 11-03-02 | 03 | 2 | COMP-04 | manual | UI filter verification | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `puppeteer/tests/test_compatibility_engine.py` — stubs for COMP-01 through COMP-04 (5 test functions)

*Existing pytest infrastructure covers all phase requirements — no framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Blueprint editor tool list filters in real-time when OS changes | COMP-04 | React state change — no Playwright tests in this phase | Open Foundry → Blueprints → Create Blueprint → change OS dropdown → verify tool list updates without page refresh |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
