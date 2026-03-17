---
phase: 25
slug: runbooks-troubleshooting
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual review + file-existence checks |
| **Config file** | none |
| **Quick run command** | `ls docs/site/runbooks/ && grep -l "root cause" docs/site/runbooks/*.md` |
| **Full suite command** | `find docs/site/ -name "*.md" | xargs grep -l "root cause" && echo "All runbooks have root cause sections"` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `ls docs/site/runbooks/ && grep -l "root cause" docs/site/runbooks/*.md`
- **After every plan wave:** Run `find docs/site/ -name "*.md" | xargs grep -l "root cause" && echo "All runbooks have root cause sections"`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 25-01-01 | 01 | 1 | RUN-01 | manual | `test -f docs/site/runbooks/node-troubleshooting.md` | ❌ W0 | ⬜ pending |
| 25-01-02 | 01 | 1 | RUN-01 | manual | `grep -c "## " docs/site/runbooks/node-troubleshooting.md` | ❌ W0 | ⬜ pending |
| 25-02-01 | 02 | 1 | RUN-02 | manual | `test -f docs/site/runbooks/job-troubleshooting.md` | ❌ W0 | ⬜ pending |
| 25-02-02 | 02 | 1 | RUN-02 | manual | `grep -c "## " docs/site/runbooks/job-troubleshooting.md` | ❌ W0 | ⬜ pending |
| 25-03-01 | 03 | 2 | RUN-03 | manual | `test -f docs/site/runbooks/foundry-troubleshooting.md` | ❌ W0 | ⬜ pending |
| 25-04-01 | 04 | 2 | RUN-04 | manual | `test -f docs/site/runbooks/faq.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `docs/site/runbooks/` directory exists
- [ ] Confirm MkDocs nav includes runbooks section

*This is a documentation-only phase — no code test framework is required.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Every runbook opens with 2-sentence root cause explanation | RUN-01, RUN-02, RUN-03 | Content quality check | Read each runbook's opening paragraph and verify it explains root cause before recovery steps |
| Node troubleshooting organized by symptom | RUN-01 | Structure review | Verify headings match observable symptoms (e.g., "Node shows offline but container is running") |
| Job troubleshooting uses concrete error messages as headers | RUN-02 | Content quality | Check section headers contain actual error strings where applicable |
| FAQ covers top misconfigurations from gap reports | RUN-04 | Cross-reference check | Compare FAQ entries against `.agent/reports/core-pipeline-gaps.md` and validation test outputs |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
