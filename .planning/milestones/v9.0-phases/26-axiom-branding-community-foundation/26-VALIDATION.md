---
phase: 26
slug: axiom-branding-community-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | grep/structural (docs-only phase — no unit tests) |
| **Config file** | none |
| **Quick run command** | `grep -r "mop-push\|Master of Puppets\|\bMoP\b" docs/docs/ --include="*.md"` |
| **Full suite command** | `docker compose -f puppeteer/compose.server.yaml build docs` |
| **Estimated runtime** | ~30 seconds (grep) / ~120 seconds (mkdocs build) |

---

## Sampling Rate

- **After every task commit:** Run grep verify for the specific term(s) that task addressed
- **After every plan wave:** Run `grep -r "mop-push\|Master of Puppets\|\bMoP\b\|Puppeteer" docs/docs/ --include="*.md"` — confirm zero remaining hits for terms that wave addressed
- **Before `/gsd:verify-work`:** `docker compose -f puppeteer/compose.server.yaml build docs` (mkdocs --strict) must pass
- **Max feedback latency:** 30 seconds (grep) / 120 seconds (docs build)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 26-01-01 | 01 | 1 | README rebrand | structural | `grep "Master of Puppets" README.md` returns 0 | ✅ | ⬜ pending |
| 26-01-02 | 01 | 1 | LICENSE check | structural | `grep "Apache" LICENSE` returns hit | ✅ | ⬜ pending |
| 26-01-03 | 01 | 1 | CONTRIBUTING.md created | structural | `test -f CONTRIBUTING.md` | ❌ W0 | ⬜ pending |
| 26-01-04 | 01 | 1 | CHANGELOG.md created | structural | `grep "^## \[" CHANGELOG.md` | ❌ W0 | ⬜ pending |
| 26-02-01 | 02 | 2 | GitHub issue templates | structural | `ls .github/ISSUE_TEMPLATE/*.md` | ❌ W0 | ⬜ pending |
| 26-02-02 | 02 | 2 | GitHub PR template | structural | `test -f .github/pull_request_template.md` | ❌ W0 | ⬜ pending |
| 26-03-01 | 03 | 3 | mop-push → axiom-push in pyproject.toml | structural | `grep "axiom-push" pyproject.toml` | ✅ | ⬜ pending |
| 26-03-02 | 03 | 3 | mop-push.md renamed | structural | `grep -r "mop-push" docs/docs/ --include="*.md"` returns 0 | ✅ | ⬜ pending |
| 26-03-03 | 03 | 3 | mkdocs build passes | structural | `docker compose -f puppeteer/compose.server.yaml build docs` | ✅ | ⬜ pending |
| 26-04-01 | 04 | 4 | Docs naming sweep | structural | `grep -ri "puppeteer\|puppet\b" docs/docs/ --include="*.md" \| wc -l` approaches 0 | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

None — no test infrastructure changes are needed. This phase creates only markdown, YAML, and a single TOML line change. Existing test suites (pytest + vitest) are not affected.

*Wave 0 tasks are file-creation tasks (CONTRIBUTING.md, CHANGELOG.md, GitHub templates) that must exist before verification commands can run.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GitHub issue templates render in UI | Community UX | Requires GitHub UI interaction | Create draft issue on GitHub — confirm template selector appears with correct options |
| GitHub PR template renders in UI | Community UX | Requires GitHub UI interaction | Create draft PR on GitHub — confirm template body pre-populates |
| CLA statement readable in CONTRIBUTING.md | Legal | Human review | Read CONTRIBUTING.md CLA section — confirm clear language and contributor acceptance instructions |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
