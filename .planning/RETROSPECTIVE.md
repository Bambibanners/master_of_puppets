# Retrospective

## Milestone: v7.0 — Advanced Foundry & Smelter

**Shipped:** 2026-03-16
**Phases:** 5 (11–15) | **Plans:** 34

### What Was Built
- Compatibility Engine — OS-family tagging on tools, two-pass blueprint validation (OS mismatch + dep confirmation), real-time tool filtering; 12/12 Playwright checks passed
- Smelter Registry — vetted ingredient catalog with CVE scanning (pip-audit), STRICT/WARNING enforcement modes, compliance badging on templates
- Package Repository Mirroring — local PyPI (pypiserver) + APT (Caddy) sidecars, auto-sync on ingredient add, air-gapped manual upload, pip.conf/sources.list injection, fail-fast enforcement at build time
- Foundry Wizard UI — 5-step guided composition wizard (Identity → Base Image → Ingredients → Tools → Review), JSON editor mode, full Smelter Registry integration
- Smelt-Check + BOM + Lifecycle — post-build ephemeral validation containers, JSON Bill of Materials capture, package index for fleet-wide BOM search, image lifecycle (ACTIVE/DEPRECATED/REVOKED) enforced at enrollment and work-pull

### What Worked
- Parallel execution of v7.0 and v8.0 phases (Phases 17-19 shipped while v7.0 was in progress) — milestones are independent enough to develop concurrently
- Soft-delete patterns (is_active, ingredient delete) caught early reduced future migration pain
- Unconditional fail-fast for mirror enforcement (separate from enforcement_mode gating) kept the two concerns cleanly separated and the behavior predictable

### What Was Inefficient
- Phase 13 required 3 gap-closure plans (13-06, 13-07, 13-08) after verification revealed missing frontend and test coverage — original 5 plans underestimated scope
- Phase 12 required 1 gap-closure plan (12-10) for SMLT-04 mirror-status enforcement gate that was missed in initial verification
- Test suite for Phase 13 failed on imports — pyproject.toml pythonpath config was missing and had to be added in gap-closure; should be a standard project convention
- ROADMAP.md became out of sync when v8.0 was archived before v7.0 completed — caused confusion at milestone close

### Patterns Established
- `pyproject.toml pythonpath=['puppeteer']` is required for test imports — document as project standard
- Sequential `side_effect` list in mock DB avoids brittle SQL-repr string matching (bound parameters make literal search unreliable)
- Gap-closure plans numbered N-06, N-07, N-08 after the N-05 verification plan — established as the standard recovery pattern

### Key Lessons
- Budget gap-closure plans in the original plan count — phases with complex service interactions (mirroring, enforcement) should expect 1-2 gap-closure plans
- Run full pytest suite after every plan, not just phase-targeted tests — regressions in adjacent modules are cheaper to catch early
- ROADMAP.md milestone ordering should match development order; shipping milestones out of order (v8.0 before v7.0) creates tracking confusion

## Milestone: v8.0 — mop-push CLI & Job Staging

**Shipped:** 2026-03-15
**Phases:** 3 (17, 18, 19) | **Plans:** 14

### What Was Built
- RFC 8628 OAuth device flow — MoP as its own IdP, browser approval page, JWT issuance
- `ScheduledJob` lifecycle status (DRAFT/ACTIVE/DEPRECATED/REVOKED) with scheduler enforcement
- `POST /api/jobs/push` upsert with dual-token verification (JWT identity + Ed25519 integrity)
- `mop-push` CLI — login, job push (DRAFT), job create (ACTIVE), Ed25519 signing locally
- Dashboard Staging tab — inspect script, finalize scheduling, one-click Publish
- OIDC v2 integration path documented in `docs/architecture/OIDC_INTEGRATION.md`

### What Worked
- Wave-based parallel plan execution kept phases fast (Phase 17 delivered in 5 plans)
- Playwright tests caught two real bugs: DASH-04 status field not persisted, PATCH route wrongly prefixed with `/api/`
- Keeping the CLI as a local `pip install ./mop_sdk` avoided PyPI complexity entirely

### What Was Inefficient
- Phase 17/18 commits landed but REQUIREMENTS.md checkboxes were never updated — required manual reconciliation at milestone close
- Dashboard build was not redeployed after Phase 19 code changes — tests initially hit stale JS

### Key Lessons
- After any backend route change, verify through the Caddy proxy (not direct to port 8001) — route prefixes interact with the `/api/*` strip rule
- Always redeploy dashboard build before running Playwright tests against the live stack
- DB migrations must be applied before restarting the agent container after schema-changing commits

## Cross-Milestone Trends

| Milestone | Phases | Plans | Key pattern |
|-----------|--------|-------|-------------|
| v7.0 | 5 | 34 | Infrastructure-heavy milestone; gap-closure plans expected for complex service phases |
| v8.0 | 3 | 14 | CLI + backend + UI in one milestone; Playwright as final gate |
