---
phase: 23
slug: getting-started-core-feature-guides
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | mkdocs build --strict (documentation smoke test) |
| **Config file** | `docs/mkdocs.yml` |
| **Quick run command** | `cd docs && mkdocs build --strict` |
| **Full suite command** | `cd docs && mkdocs build --strict 2>&1 | tail -5` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd docs && mkdocs build --strict`
- **After every plan wave:** Run `cd docs && mkdocs build --strict 2>&1 | tail -5`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 23-01-01 | 01 | 1 | GUIDE-01 | smoke | `cd docs && mkdocs build --strict` | ❌ Wave 0 | ⬜ pending |
| 23-01-02 | 01 | 1 | GUIDE-01 | smoke | `cd docs && mkdocs build --strict` | ❌ Wave 0 | ⬜ pending |
| 23-02-01 | 02 | 1 | GUIDE-02 | smoke | `cd docs && mkdocs build --strict` | ❌ Wave 0 | ⬜ pending |
| 23-03-01 | 03 | 2 | FEAT-01 | smoke | `cd docs && mkdocs build --strict` | ❌ Wave 0 | ⬜ pending |
| 23-04-01 | 04 | 2 | FEAT-02 | smoke | `cd docs && mkdocs build --strict` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `docs/docs/getting-started/prerequisites.md` — stub for GUIDE-02
- [ ] `docs/docs/getting-started/install.md` — stub for GUIDE-01
- [ ] `docs/docs/getting-started/enroll-node.md` — stub for GUIDE-01
- [ ] `docs/docs/getting-started/first-job.md` — stub for GUIDE-01
- [ ] `docs/docs/feature-guides/foundry.md` — stub for FEAT-01
- [ ] `docs/docs/feature-guides/mop-push.md` — stub for FEAT-02
- [ ] `docs/docs/security/index.md` — nav stub (mkdocs --strict requires file)
- [ ] `docs/docs/runbooks/index.md` — nav stub (mkdocs --strict requires file)

*Note: Phase 23 is documentation-only. All validation is build-time (`mkdocs build --strict`) — no unit tests required.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Getting started guide is a single linear walkthrough (no section-jumping) | GUIDE-01 | Requires human reading for flow assessment | Read prerequisites.md → install.md → enroll-node.md → first-job.md in order; confirm no forward references to later sections |
| Foundry guide wizard steps match actual UI (5 steps: Identity, Base Image, Ingredients, Tools, Review) | FEAT-01 | UI label accuracy requires visual comparison | Open dashboard Foundry page, compare wizard labels to guide text |
| mop-push CLI commands produce expected output | FEAT-02 | Requires live CLI install and execution | Run `pip install -e .` from repo root, execute `mop-push --help` to verify entry point |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
