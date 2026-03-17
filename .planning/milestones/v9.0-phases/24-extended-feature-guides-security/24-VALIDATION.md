---
phase: 24
slug: extended-feature-guides-security
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | mkdocs build (primary), pytest (existing backend suite) |
| **Config file** | `docs/mkdocs.yml` |
| **Quick run command** | `cd docs && mkdocs build 2>&1 \| grep -i warning` |
| **Full suite command** | `docker compose -f puppeteer/compose.server.yaml build docs` |
| **Estimated runtime** | ~10 seconds (quick), ~60 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `cd docs && mkdocs build 2>&1 | grep -i warning` (catches broken links/missing files)
- **After every plan wave:** Run full Docker build of docs container (`--strict` mode)
- **Before `/gsd:verify-work`:** Full suite must be green (all 9 files exist, nav resolves, Docker build passes)
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 24-01-01 | 01 | 1 | FEAT-03 | build check | `cd docs && mkdocs build 2>&1 \| grep -i warning` | ❌ W0 | ⬜ pending |
| 24-02-01 | 02 | 1 | FEAT-04 | build check | `cd docs && mkdocs build 2>&1 \| grep -i warning` | ❌ W0 | ⬜ pending |
| 24-03-01 | 03 | 1 | FEAT-05 | build check | `cd docs && mkdocs build 2>&1 \| grep -i warning` | ❌ W0 | ⬜ pending |
| 24-04-01 | 04 | 1 | SECU-01 | build check | `cd docs && mkdocs build 2>&1 \| grep -i warning` | ❌ W0 | ⬜ pending |
| 24-05-01 | 05 | 2 | SECU-02, SECU-03, SECU-04 | build check | `cd docs && mkdocs build 2>&1 \| grep -i warning` | ❌ W0 | ⬜ pending |
| 24-nav | 05 | 2 | All | strict build | `docker compose -f puppeteer/compose.server.yaml build docs` | ✅ existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `docs/docs/feature-guides/job-scheduling.md` — stub required before nav entry added (FEAT-03)
- [ ] `docs/docs/feature-guides/rbac.md` — stub required (FEAT-04)
- [ ] `docs/docs/feature-guides/oauth.md` — stub required (FEAT-05)
- [ ] `docs/docs/feature-guides/rbac-reference.md` — stub required (FEAT-04 reference)
- [ ] `docs/docs/security/mtls.md` — stub required (SECU-01)
- [ ] `docs/docs/security/rbac-hardening.md` — stub required (SECU-02)
- [ ] `docs/docs/security/audit-log.md` — stub required (SECU-03)
- [ ] `docs/docs/security/air-gap.md` — stub required (SECU-04)

*Note: `security/index.md` already exists — replace stub content, no new file needed for nav.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Cron field order in job-scheduling guide matches scheduler_service.py | FEAT-03 | Documentation accuracy — no automated test possible | Compare guide cron table against `scheduler_service.py:93` |
| Permission table in rbac.md matches startup seed | FEAT-04 | Documentation accuracy | Compare guide table against `main.py:174-188` |
| Device flow TTL/interval values in oauth.md match code | FEAT-05 | Documentation accuracy | Compare against `main.py:781-782` |
| Cert validity periods in mtls.md match pki.py | SECU-01 | Documentation accuracy | Compare against `pki.py:136` |
| API key scoped permissions documented as "reserved/future use" | FEAT-05 | Guard against misleading docs | Confirm `UserApiKey.permissions` caveat present in oauth.md |
| Cert rotation procedure: verify new cert active before revoking old | SECU-01 | Safety-critical procedure | Confirm danger admonition present with prerequisite checklist |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
