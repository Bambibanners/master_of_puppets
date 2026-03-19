---
phase: 34
slug: ce-baseline-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 34 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `.worktrees/axiom-split/pyproject.toml` |
| **Quick run command** | `cd .worktrees/axiom-split && pytest puppeteer/agent_service/tests/ -m "not ee_only" -x -q` |
| **Full suite command** | `cd .worktrees/axiom-split && pytest -m "not ee_only" -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd .worktrees/axiom-split && pytest puppeteer/agent_service/tests/ -m "not ee_only" -x -q`
- **After every plan wave:** Run `cd .worktrees/axiom-split && pytest -m "not ee_only" -q`
- **Before `/gsd:verify-work`:** Full suite must be green (zero failures, zero EE-attribute errors)
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 34-01-01 | 01 | 0 | GAP-03 | unit (marker) | `cd .worktrees/axiom-split && pytest puppeteer/agent_service/tests/ -m "not ee_only" -v` | ❌ W0 | ⬜ pending |
| 34-01-02 | 01 | 0 | GAP-02 | unit | `cd .worktrees/axiom-split && pytest puppeteer/agent_service/tests/ -k "ee_plugin" -x` | ❌ W0 | ⬜ pending |
| 34-02-01 | 02 | 1 | GAP-01 | integration (HTTP) | `cd .worktrees/axiom-split && pytest puppeteer/agent_service/tests/test_main.py -k "402 or stub" -x` | ✅ | ⬜ pending |
| 34-02-02 | 02 | 1 | GAP-02 | unit | `cd .worktrees/axiom-split && pytest puppeteer/agent_service/tests/ -k "ee_plugin" -x` | ❌ W0 | ⬜ pending |
| 34-03-01 | 03 | 1 | GAP-04 | unit | `cd .worktrees/axiom-split && pytest puppeteer/agent_service/tests/ puppeteer/tests/ -m "not ee_only" -x` | ✅ | ⬜ pending |
| 34-04-01 | 04 | 1 | GAP-05 | unit | `cd .worktrees/axiom-split && pytest puppeteer/agent_service/tests/test_models.py -x` | ✅ | ⬜ pending |
| 34-04-02 | 04 | 1 | GAP-06 | unit | `cd .worktrees/axiom-split && pytest puppeteer/agent_service/tests/test_job_service.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `puppeteer/agent_service/tests/test_lifecycle_enforcement.py` — ee_only placeholder stub for GAP-03
- [ ] `puppeteer/agent_service/tests/test_foundry_mirror.py` — ee_only placeholder stub for GAP-03
- [ ] `puppeteer/agent_service/tests/test_smelter.py` — ee_only placeholder stub for GAP-03
- [ ] `puppeteer/agent_service/tests/test_staging.py` — ee_only placeholder stub for GAP-03
- [ ] New `test_ee_plugin_loader()` test case in `test_main.py` or new file — covers GAP-01 + GAP-02

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `GET /api/features` returns all flags as `false` on CE install | GAP-01 | Requires live CE server | Start server with `EDITION=ce`, `curl https://localhost:8001/api/features` — verify all values are `false` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
