---
phase: 28
slug: infrastructure-gap-closure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Docker build + grep (no unit test framework applicable) |
| **Config file** | `docs/Dockerfile` (builder stage runs `mkdocs build --strict`) |
| **Quick run command** | `docker compose -f puppeteer/compose.server.yaml build docs` |
| **Full suite command** | Build + CDN grep scan (see Per-Task map below) |
| **Estimated runtime** | ~60–90 seconds (Docker build with mkdocs) |

---

## Sampling Rate

- **After every task commit:** Run `docker compose -f puppeteer/compose.server.yaml build docs`
- **After every plan wave:** Run full suite (build + CDN grep scan)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 28-01-01 | 01 | 1 | INFRA-06 | build | `docker compose -f puppeteer/compose.server.yaml build docs` | ✅ existing | ⬜ pending |
| 28-01-02 | 01 | 1 | INFRA-06 | grep scan | `docker run --rm localhost/master-of-puppets-docs:v1 sh -c "grep -rq 'fonts.googleapis.com\|cdn.jsdelivr.net\|cdnjs.cloudflare.com' /usr/share/nginx/html && echo FAIL || echo PASS"` | N/A — runtime | ⬜ pending |
| 28-01-03 | 01 | 1 | SECU-04 | manual | Read `docs/docs/security/air-gap.md` — confirm plugin references are accurate | ✅ existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files, fixtures, or framework installs required.

*mkdocs build --strict is already enforced in `docs/Dockerfile` builder stage.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Air-gap guide accurately references privacy + offline plugins | SECU-04 | Content review — no automated content correctness check | Read `docs/docs/security/air-gap.md`, confirm it mentions privacy + offline plugins as the CDN-free mechanism |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
