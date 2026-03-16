---
phase: 21
slug: api-reference-dashboard-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) + vitest (frontend) |
| **Config file** | `puppeteer/pytest.ini` / `puppeteer/dashboard/vite.config.ts` |
| **Quick run command** | `cd puppeteer && pytest tests/ -x -q` |
| **Full suite command** | `cd puppeteer && pytest && cd dashboard && npm run test` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd puppeteer && pytest tests/ -x -q`
- **After every plan wave:** Run `cd puppeteer && pytest && cd dashboard && npm run test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | APIREF-01 | unit | `cd puppeteer && python scripts/export_openapi.py && test -f docs/docs/api-reference/openapi.json` | ❌ W0 | ⬜ pending |
| 21-01-02 | 01 | 1 | APIREF-02 | build | `docker build --target export -t mop-docs-export . && echo BUILD_OK` | ❌ W0 | ⬜ pending |
| 21-01-03 | 01 | 1 | APIREF-03 | manual | See manual verifications | N/A | ⬜ pending |
| 21-01-04 | 01 | 1 | APIREF-01 | unit | `grep -q 'swagger-ui' docs/docs/api-reference.md` | ❌ W0 | ⬜ pending |
| 21-02-01 | 02 | 2 | DASH-01 | unit | `cd puppeteer/dashboard && npm run test -- --run` | ✅ | ⬜ pending |
| 21-02-02 | 02 | 2 | DASH-02 | unit | `cd puppeteer/dashboard && npm run test -- --run` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `puppeteer/tests/test_openapi_export.py` — test that export_openapi.py produces valid JSON with expected routes
- [ ] `puppeteer/dashboard/src/views/__tests__/Navigation.test.tsx` — test sidebar has external /docs/ link, no Docs route

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Swagger UI renders with no CDN requests | APIREF-01 | Requires browser network inspector | Open `/docs/api-reference/`, open DevTools Network tab, check no requests to CDN domains (unpkg.com, jsdelivr.net, etc.) |
| Routes grouped by tag in Swagger UI | APIREF-03 | Visual rendering check | Load `/docs/api-reference/`, verify endpoints appear under named groups (not all under "default") |
| Docs sidebar opens new tab | DASH-01 | Browser behavior check | Click "Docs" in sidebar, verify `/docs/` opens in new tab not current tab |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
