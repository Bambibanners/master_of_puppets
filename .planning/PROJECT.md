# Master of Puppets

## What This Is

A secure, fully-featured task and job scheduler built for hostile environments. A central orchestrator ("Puppeteer") manages a mesh of worker nodes ("Puppets") using a pull architecture — nodes poll for work according to their declared capabilities. Security is structural, not bolted-on: mTLS between all components, Ed25519-signed scripts required before execution, all jobs isolated in containers inside the puppet's environment.

Targets homelab and enterprise internal deployments where nodes may be shared or partially untrusted. Designed to integrate with CI/CD pipelines for environment-tagged deployment promotion (DEV → TEST → PROD).

## Core Value

Jobs run reliably — on the right node, when scheduled, with their output captured — without any step in the chain weakening the security model.

## Requirements

### Validated

- ✓ mTLS node enrollment (Root CA, client cert signing, CRL revocation) — existing
- ✓ Ed25519 job signing — scripts verified before execution — existing
- ✓ Container-isolated job execution (Docker/Podman, configurable mode) — existing
- ✓ Pull architecture — nodes poll `/work/pull`, orchestrator never pushes — existing
- ✓ Node capability matching (runtime, OS) for job targeting — existing
- ✓ Explicit node/group targeting alongside capability matching — existing
- ✓ RBAC with admin / operator / viewer roles (DB-backed permissions) — existing
- ✓ Web dashboard (React) + REST API (FastAPI) — existing
- ✓ Cron-scheduled job definitions (APScheduler) — existing
- ✓ Foundry: build custom node images from runtime + network blueprints — existing
- ✓ Node stats history + sparkline monitoring — existing
- ✓ Full audit log for security-relevant events — existing
- ✓ Service principals + API keys for machine-to-machine auth — existing
- ✓ OAuth device flow (RFC 8628) — MoP-native IdP, browser approval, JWT issuance — v8.0
- ✓ `mop-push` CLI — login/push/create, Ed25519 signing locally, private key never transmitted — v8.0
- ✓ Job lifecycle status (DRAFT/ACTIVE/DEPRECATED/REVOKED) + REVOKED dispatch enforcement — v8.0
- ✓ Dashboard Staging view — inspect drafts, finalize scheduling, one-click Publish — v8.0
- ✓ Foundry Compatibility Engine — OS-family tagging, runtime deps, two-pass blueprint validation, real-time tool filtering — v7.0
- ✓ Smelter Registry — vetted ingredient catalog, CVE scanning (pip-audit), STRICT/WARNING enforcement, compliance badging — v7.0
- ✓ Package Repository Mirroring — local PyPI + APT sidecars, auto-sync, air-gapped upload, pip.conf/sources.list injection, fail-fast — v7.0
- ✓ Foundry Wizard UI — 5-step guided composition wizard with OS filtering and Smelter integration — v7.0
- ✓ Smelt-Check + BOM + Image Lifecycle — post-build validation, JSON BOM, package index, ACTIVE/DEPRECATED/REVOKED enforcement — v7.0

### Active — v9.0 Enterprise Documentation

- [ ] MkDocs Material container — docs service in compose.server.yaml, git-backed markdown in `docs/`
- [ ] Dashboard integration — replace in-app Docs view with link/redirect to docs container
- [ ] Auto-generated API reference — built from FastAPI's `/openapi.json`, rendered in MkDocs
- [ ] Developer documentation — architecture guide, setup & deployment, contributing guide
- [ ] User getting started guide — end-to-end first-run walkthrough (install → node → job)
- [ ] Feature guides — Foundry, Smelter, mop-push CLI, job scheduling, RBAC, OAuth, Staging
- [ ] Security & compliance guide — mTLS setup, cert rotation, RBAC config, audit log, air-gap
- [ ] Runbooks & troubleshooting — common failures, node recovery, cert issues, FAQ

### Planned — Future Milestones

- [ ] Job output capture — stdout/stderr, exit codes, per-execution records
- [ ] Execution history — queryable timeline of past runs per job and per node
- [ ] Retry policy — configurable retries on failure (count, backoff strategy)
- [ ] Job dependencies — job B runs only after job A succeeds
- [ ] Environment node tags — DEV / TEST / PROD tags for CI/CD promotion targeting
- [ ] CI/CD API integration — documented, machine-friendly endpoints for dispatching jobs from pipelines
- [ ] Conditional triggers — run job based on outcome of previous job or external signal
- [ ] SLSA provenance — Ed25519-signed build provenance, resource limits, --secret credentials (deferred from v7.0)

### Out of Scope

- Mobile app — web-first, API covers automation needs
- Silent security weakening — any trade-off must be explicitly documented and operator opt-in
- Built-in secrets management beyond Fernet-at-rest — use external vault for production secrets
- Real-time collaborative editing of scripts — single author, versioned by signing

## Context

Existing codebase is functional and deployed. Backend is FastAPI + SQLAlchemy (SQLite dev, Postgres prod). Frontend is React/Vite. Node agent is Python, runs inside Docker. Infrastructure uses Caddy (TLS termination) + Cloudflare tunnel for dashboard access.

Known deferred issues: SQLite NodeStats pruning compat (MIN-6), Foundry build dir cleanup (MIN-7), per-request DB query in require_permission (MIN-8), non-deterministic node ID scan order (WARN-8). See `.agent/reports/core-pipeline-gaps.md`.

The security model is zero-trust by default. Any feature that requires relaxing mTLS, skipping signature verification, or running jobs outside containers must be treated as a configuration option with explicit documentation of the risk — never a code default.

## Constraints

- **Security**: mTLS + signed code + container isolation are non-negotiable architectural constants. Trade-offs may be documented for operator opt-in but never silently defaulted.
- **Tech stack**: FastAPI (Python) backend, React/TypeScript frontend, SQLAlchemy ORM. No migrations framework — `create_all` at startup, manual ALTER for existing DBs.
- **Execution model**: Pull-only. Orchestrator never initiates connections to nodes. Nodes are stateless between polls.
- **Compatibility**: SQLite for dev/homelab, Postgres for production. New features must work on both.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Pull architecture (nodes poll orchestrator) | No inbound firewall rules on nodes; works across NAT/hostile networks | ✓ Good |
| Ed25519 signing required for all jobs | Prevents arbitrary code execution even if orchestrator is compromised | ✓ Good |
| Container-per-job isolation | Memory leak containment, runtime isolation, OS-level security boundary | ✓ Good |
| RBAC seeded from DB, not config files | Supports org-wide teams without redeployment | ✓ Good |
| Environment tags for CI/CD targeting | Enables DEV→TEST→PROD promotion patterns without separate orchestrator instances | — Pending |
| Job output stored server-side | Nodes are stateless — results must flow back to orchestrator | — Pending |
| MoP-native OAuth device flow (not external OIDC) | Avoids external IdP dependency for v1; OIDC documented as v2 path | ✓ Good |
| Job staging (DRAFT→ACTIVE via dashboard) | Operators review and finalize scheduling before jobs run in production | ✓ Good |
| Private key stays on operator machine | Ed25519 signing in CLI; only signature transmitted to server | ✓ Good |
| Soft-delete for CapabilityMatrix tools | Preserves tool history; reversible; admin can view inactive entries | ✓ Good |
| Smelter enforcement_mode in Config table | No new table; reuses existing key/value store; runtime-configurable | ✓ Good |
| Mirror fail-fast unconditional (enforcement_mode gates only unapproved check) | Prevents silent external fetching; two separate enforcement concerns | ✓ Good |
| Soft-purge for ingredient delete | Preserves mirror files and audit history; is_active=False flag | ✓ Good |
| Image lifecycle status (ACTIVE/DEPRECATED/REVOKED) on puppet_templates | Enrollment and work-pull enforcement without DB joins; status is the authority | ✓ Good |
| Phase 16 (Security & Governance) deferred | No production blockers; provenance/--secret deferred to avoid over-engineering v7.0 | ⚠️ Revisit |

## Current Milestone: v9.0 Enterprise Documentation

**Goal:** Bring all technical and user documentation to enterprise standard, hosted as a containerised MkDocs wiki within the stack and linked from the dashboard.

**Target features:**
- MkDocs Material container — standalone docs service in compose.server.yaml, git-backed markdown, portable
- Dashboard integration — replace existing in-app Docs view with link to the docs container
- Auto-generated API reference — OpenAPI-driven, always in sync with the code
- Developer documentation — architecture guide, setup/deployment, contributing guide
- User documentation — getting started E2E walkthrough, per-feature guides, security & compliance, runbooks/troubleshooting

## Current State — v7.0, v8.0 & v9.0 In Progress (2026-03-16)

The Foundry is now a fully governed build pipeline. Operators compose images through a 5-step wizard that filters tools by OS family and sources packages from the Smelter Registry. Every build is validated by an ephemeral Smelt-Check container, produces a JSON Bill of Materials, and carries a lifecycle status (ACTIVE/DEPRECATED/REVOKED) enforced at node enrollment and job dispatch.

In parallel, the operator toolchain gained `mop-push` (v8.0): sign and push jobs from the terminal, review in the Staging dashboard, publish with one click. The full job lifecycle (DRAFT → ACTIVE → DEPRECATED → REVOKED) is enforced at dispatch.

**Shipped in v7.0:** Compatibility Engine, Smelter Registry (CVE scanning + enforcement), Package Mirroring (PyPI + APT sidecars), Foundry Wizard UI, Smelt-Check + BOM + Lifecycle.
**Shipped in v8.0:** OAuth device flow, `mop-push` CLI, job lifecycle status, Dashboard Staging view, OIDC v2 architecture doc.

---
*Last updated: 2026-03-16 after v8.0 milestone — v9.0 started*
