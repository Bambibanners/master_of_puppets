# Phase 22: Developer Documentation - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Write three developer-facing guides in the MkDocs site (`docs/docs/`): an architecture guide (full technical deep-dive with Mermaid diagrams), a setup & deployment guide (operator-first, with local dev section), and a contributing guide (test requirements, linting standards, migration pattern). Also cleans up all legacy documentation files that predate the MkDocs setup.

</domain>

<decisions>
## Implementation Decisions

### Legacy content cleanup
- Write all three guides fresh from scratch — do not port content from old files
- Delete all old documentation files in this phase (not deferred):
  - `docs/architecture.md`, `docs/INSTALL.md`, `docs/deployment_guide.md`, `docs/SDK_GUIDE.md`, `docs/UserGuide.md`, `docs/scheduling.md`, `docs/security.md`, `docs/security_signatures.md`, `docs/ssl_guide.md`, `docs/compatibility.md`, `docs/REMOTE_DEPLOYMENT.md`, `docs/third_party_audit_report.md`
  - `puppeteer/docs/` directory and all its contents
- The new MkDocs site (`docs/docs/`) is the canonical and sole documentation location

### MkDocs nav placement
- All three guides go under a `Developer` section in `mkdocs.yml` nav
- Consistent with the audience-oriented nav structure established in STATE.md
- Nav entry: `Developer:` → `Architecture`, `Setup & Deployment`, `Contributing`

### Architecture guide — full technical deep-dive
- **Level of detail:** Full technical deep-dive (not a high-level overview)
- **Diagrams:** 4+ Mermaid diagrams — minimum: system overview, mTLS enrollment sequence, job execution data flow, at least one more (DB schema, RBAC model, or Foundry build flow)
- **Topics to cover:**
  - All services explained: agent_service, model_service (scheduler), job_service, foundry_service, scheduler_service, pki_service, signature_service — what each does
  - DB schema / data model: key tables and relationships (Job, Node, ScheduledJob, PuppetTemplate, Blueprint, etc.)
  - Security model deep-dive: mTLS cert lifecycle, Ed25519 signing chain, RBAC permission model, JWT + token versioning, Fernet encryption at rest
  - Foundry & Smelter: image build pipeline, blueprint/template model, CVE scanning, BOM, image lifecycle enforcement

### Setup & deployment guide — operator-first
- **Structure:** Operator path first (Docker Compose production), then local dev section
- **Quick start block:** 5-command runnable block at the very top — gets anyone to a running stack without reading further
- **Env vars documentation:** Document ALL required env vars (SECRET_KEY, ENCRYPTION_KEY, ADMIN_PASSWORD, DATABASE_URL, API_KEY, etc.) with placeholder example values + note on how to generate secure values; docs are behind CF Access so this is safe
- **TLS bootstrap:** Brief coverage — where to find JOIN_TOKEN in dashboard, how to set AGENT_URL on a node; deep cert rotation/revocation lives in Phase 24 Security guide (link to it)
- **DEVDOC-02 success criterion:** A developer following this guide on a clean machine can reach a running local stack (SQLite + backend + dashboard) without consulting the codebase

### Contributing guide — explicit PR bar
- **Tests required to merge:** Both must pass:
  - Backend: `cd puppeteer && pytest` — clean run
  - Frontend: `cd puppeteer/dashboard && npm run test` — clean run
  - No numeric coverage threshold — green is the bar
- **Code style:**
  - Python: **Black** (formatting) + **Ruff** (linting)
  - Frontend: **ESLint** (`npm run lint`) — already configured
  - Add `pyproject.toml` with Black + Ruff config to the repo as part of this phase
- **Database migration pattern:** Dedicated section — "No Alembic: adding DB columns requires a `migration_vN.sql` file with `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements; `create_all` will NOT alter existing tables on existing deployments"
- **DEVDOC-03 success criterion:** Guide specifies exactly how to run tests and what a passing PR requires

### Claude's Discretion
- Exact Mermaid diagram syntax and styling
- Section ordering within each guide beyond the structural decisions above
- Tone and formatting conventions (consistent with MkDocs Material best practices)
- Which additional diagram(s) beyond the 3 required ones to include (DB schema, RBAC, or Foundry flow)
- `pyproject.toml` Ruff rule selection (sensible defaults, not overly strict)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/docs/index.md`: Placeholder index already in place — stays untouched
- `docs/docs/api-reference/`: Already populated by Phase 21 — stays untouched
- `docs/mkdocs.yml`: Needs `nav:` section added; currently has no nav defined

### Established Patterns
- MkDocs content lives in `docs/docs/` (NOT `docs/` root)
- `mkdocs build --strict` enforced — all linked files must exist, no broken refs
- Two-stage Dockerfile in `docs/Dockerfile` — content phases just add markdown files; no Dockerfile changes needed
- Privacy + offline plugins already enabled — no external CDN assets at runtime

### Integration Points
- `docs/mkdocs.yml`: Add `nav:` section with `Developer:` subsection
- `docs/docs/`: Add `developer/` subdirectory with 3 new markdown files
- `puppeteer/pyproject.toml` (new): Black + Ruff config
- File deletions: all legacy `docs/*.md` files and `puppeteer/docs/` directory

</code_context>

<specifics>
## Specific Ideas

- The architecture guide should be thorough enough that a new contributor can understand the entire system without reading the code — "full technical deep-dive" was explicitly chosen over a high-level overview
- Operator-first structure for the setup guide: most readers will be deploying, not contributing; local dev is a secondary section
- Quick start block must be truly runnable (not pseudo-code) — verifiable against the actual CLAUDE.md commands which are already correct
- Contributing guide must explicitly mention the no-Alembic migration pattern as a "major contributor gotcha"
- Black + Ruff config files (`pyproject.toml`) should be added to the repo as part of this phase — establishing the standard in code, not just in docs

</specifics>

<deferred>
## Deferred Ideas

- **Reformatting existing Python codebase with Black + Ruff** — Phase 22 adds the config files and documents the standard; actually running `black .` and `ruff --fix .` on all existing code is a separate housekeeping task (future phase or standalone task)
- All other legacy doc content (security guides, feature guides, runbooks) — covered by Phases 23-25

</deferred>

---

*Phase: 22-developer-documentation*
*Context gathered: 2026-03-16*
