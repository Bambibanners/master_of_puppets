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

## Milestone: v9.0 — Enterprise Documentation

**Shipped:** 2026-03-17
**Phases:** 9 (20–28) | **Plans:** 27

### What Was Built
- MkDocs Material docs site at `/docs/` — two-stage Dockerfile, Caddy routing, air-gapped (CDN-free via privacy + offline plugins)
- Auto-generated API reference from FastAPI OpenAPI schema at container build time
- Complete operator documentation: getting started E2E walkthrough, all 7 feature guides, security & compliance (mTLS, RBAC, audit, air-gap), symptom-first runbooks and FAQ
- Axiom rebranding: CLI renamed `axiom-push`, README, CONTRIBUTING, CHANGELOG, GitHub community health files, full MkDocs naming pass
- GitHub Actions CI/CD pipelines for multi-arch GHCR and PyPI OIDC release

### What Worked
- Stub-first nav pattern: create all stub files before content plans so `mkdocs build --strict` passes throughout — no broken builds between plans
- Admonition-as-gotcha pattern: warning/danger admonitions for known operator failure modes inline with the relevant step (not in a separate "Gotchas" section)
- Wave-based parallel execution: Phase 24 and 25 each delivered 4-5 guides in parallel waves without conflicts
- Symptom-first framing for runbooks: H3 headers are observable states ("Node shows offline but container is running") not component names — immediately searchable by operators in distress
- The CDN verification pattern (https:// prefix match vs. bare domain) caught a real false positive that would have shipped a broken air-gap claim

### What Was Inefficient
- INFRA-06 gap closure (Phase 28) was caused by a regression in Phase 22 that should have been caught at plan verification time — the privacy/offline plugin configuration was an explicit requirement in the Phase 20 plan
- ROADMAP.md milestones header was stale (listed "Phases 20-25, 28" missing 26 and 27) because phases were added late
- PyPI Trusted Publisher setup required manual org creation outside the milestone scope — this dependency should have been identified and either resolved or explicitly deferred before Phase 27 was planned

### Patterns Established
- `npx vitest run` (not `npm run test`) in CI to avoid watch mode hang
- id-token:write scoped per-job to PyPI publish jobs only — not at workflow level
- CDN verification: `grep -rq 'https://fonts.googleapis.com\|https://cdn.jsdelivr.net' /usr/share/nginx/html && echo FAIL || echo PASS`
- Docs container dummy env vars: `postgresql+asyncpg://dummy/dummy` and `API_KEY=dummy` required in Dockerfile builder stage for openapi.json generation
- Plugin ordering locked: `search → privacy → offline → swagger-ui-tag`

### Key Lessons
- Plan for dependency validation before documentation phases — if a guide describes a feature, verify the feature is actually in the state the guide claims (air-gap guide + INFRA-06)
- For branding milestones, do a grep pass for the old name before calling the phase complete — 21 docs files is a lot to audit manually
- PyPI/GitHub org dependencies should be explicit "pre-flight checklist" items at the start of a distribution phase, not discovered at the end

### Cost Observations
- 9 phases, 27 plans, 134 commits in 2 days
- Primarily documentation work — heavy on write/edit operations, light on Bash execution compared to infrastructure milestones
- Wave-based parallel execution effective: phases with 4-5 plans completed in the same number of agent invocations as phases with 2 plans

## Cross-Milestone Trends

| Milestone | Phases | Plans | Key pattern |
|-----------|--------|-------|-------------|
| v7.0 | 5 | 34 | Infrastructure-heavy; gap-closure plans expected for complex service interactions |
| v8.0 | 3 | 14 | CLI + backend + UI in one milestone; Playwright as final gate |
| v9.0 | 9 | 27 | Documentation milestone; stub-first nav pattern; regression gap closure required |
