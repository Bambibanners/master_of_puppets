# Milestones

## v7.0 Advanced Foundry & Smelter (Shipped: 2026-03-16)

**Phases completed:** 5 phases (11–15), 34 plans

**Key accomplishments:**
- Compatibility Engine — OS-family tagging on tools, two-pass blueprint validation (OS mismatch + dep confirmation), real-time tool filtering in blueprint creation; 12/12 Playwright checks passed
- Smelter Registry — vetted ingredient catalog with CVE scanning (pip-audit), STRICT/WARNING enforcement, compliance badging on templates; blocks non-compliant builds at Foundry
- Package Repository Mirroring — local PyPI (pypiserver) + APT (Caddy) sidecars, auto-sync on ingredient add, air-gapped manual upload, pip.conf/sources.list injection; fail-fast enforcement at build time
- Foundry Wizard UI — 5-step guided composition wizard (Identity → Base Image → Ingredients → Tools → Review), JSON editor for power users, full Smelter Registry integration for ingredient picking
- Smelt-Check + BOM + Lifecycle — post-build ephemeral validation containers, JSON Bill of Materials capture, package index for fleet-wide BOM search, image lifecycle (ACTIVE/DEPRECATED/REVOKED) enforced at enrollment and work-pull

---

## v8.0 mop-push CLI & Job Staging (Shipped: 2026-03-15)

**Phases completed:** 3 phases (17–19), 14 plans

**Key accomplishments:**
- OAuth Device Flow (RFC 8628) — MoP-native IdP, browser approval page, JWT issuance; no external IdP dependency
- mop-push CLI — login/push/create commands, Ed25519 signing locally, private key never transmitted; installable as SDK package
- Job lifecycle status (DRAFT/ACTIVE/DEPRECATED/REVOKED) — full state machine with REVOKED enforcement at dispatch
- Dashboard Staging view — inspect drafts, finalize scheduling, one-click Publish; operators review before jobs run
- OIDC v2 architecture doc — documents future external IdP integration path

---

## v9.0 Enterprise Documentation (Shipped: 2026-03-17)

**Phases completed:** 9 phases (20–28), 27 plans
**Git range:** `b9796c3` → `110feb8` (134 commits, 173 files, +22,548 / -1,741 lines)

**Key accomplishments:**
- Docs container — MkDocs Material at `/docs/`, two-stage Dockerfile (python:3.12-slim builder + nginx:alpine), Caddy routing, CDN-free (privacy + offline plugins download all Google Fonts/CDN assets at build time)
- Auto-generated API reference — FastAPI OpenAPI schema exported at container build time (no running server), Swagger UI rendered in MkDocs with 17 tag groups
- Developer documentation — architecture guide with Mermaid diagrams, setup & deployment guide, contributing guide with Black/Ruff setup and no-Alembic warning
- Complete operator documentation — end-to-end getting started walkthrough + Foundry, axiom-push CLI, job scheduling, RBAC, OAuth feature guides; mTLS, RBAC hardening, audit log, air-gap security guides
- Runbooks & FAQ — symptom-first troubleshooting for nodes, jobs, and Foundry; unified FAQ with all 4 required gotchas (blueprint dict format, EXECUTION_MODE=direct, JOIN_TOKEN, ADMIN_PASSWORD)
- Axiom rebranding — CLI renamed `axiom-push`, README rewrite (<80 lines, links to docs), CONTRIBUTING + CHANGELOG + GitHub community health files, full MkDocs naming pass across 21 docs files
- CI/CD pipelines — GitHub Actions CI (pytest matrix + vitest + docker-validate) + release workflow (multi-arch GHCR + PyPI OIDC); PyPI Trusted Publisher setup deferred pending org creation

---

