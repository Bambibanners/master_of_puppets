# Phase 27: CI/CD, Packaging & Distribution - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Automate testing, building, and distribution of Axiom artifacts via GitHub Actions. CI runs tests on every PR and push to main. A release pipeline (triggered by `v*` tag) builds and pushes the orchestrator Docker image to GHCR and publishes `axiom-sdk` to PyPI. Installer scripts are rebranded from MoP to Axiom. The docs site is updated to feature the curl-from-orchestrator node install path prominently.

Internal code identifiers, API routes, and DB table names are NOT changed in this phase.

</domain>

<decisions>
## Implementation Decisions

### CI triggers and scope

- Triggers: PRs + push to `main`
- Test suites run on CI:
  - Backend: `pytest` in `puppeteer/`
  - Frontend: `vitest` (`npm run test`) in `puppeteer/dashboard/`
  - Frontend lint: `npm run lint`
  - Docker build validation: `docker build` on Containerfile.server (no push — just confirms image compiles)
- Python matrix: 3.10, 3.11, 3.12 (all three, matching `requires-python = ">=3.10"` in pyproject.toml)
- Database in CI: SQLite only — no Postgres service container needed

### Docker image release

- Registry: GHCR only — `ghcr.io/axiom-laboratories/axiom`
- CE/EE: CE image only for now — EE features not yet implemented
- Release trigger: git tag push matching `v*` (e.g., `v1.0.0-alpha`, `v1.0.0`)
- Image tags on release: semver + `latest` (e.g., `1.0.0-alpha` AND `latest`)
- Published images: orchestrator only (Containerfile.server) — node image NOT published to registry
- Architectures: `linux/amd64` + `linux/arm64` via QEMU/buildx
- Build caching: GitHub Actions cache (`type=gha`) for meaningful speedup on repeated builds
- Secrets: runtime-only — no build-time ARG secrets needed (ENCRYPTION_KEY, SECRET_KEY, etc. are all injected at runtime via env vars)

### PyPI publishing

- Trigger: same `v*` git tag as Docker release — one tag = full release (Docker + PyPI)
- Target: TestPyPI first to validate install, then real PyPI
- Package contents: `mop_sdk/` only — the existing package that provides the `axiom-push` CLI
- Auth: PyPI Trusted Publisher (OIDC) — no long-lived API token stored in GitHub Secrets
- Version bump: manual edit to `pyproject.toml` before tagging — developer edits version, commits, pushes `v*` tag
- Pre-release handling: publish `1.0.0-alpha` (PEP 440: `1.0.0a1`) as-is — pre-release flag means `pip install` won't pull it by default without `--pre`

### Installer scripts rebranding

- Rebrand `install_universal.sh`, `install_node.sh`, `install_universal.ps1` — replace "Master of Puppets" / "MoP" branding in script banners, comments, and output strings with "Axiom"
- The orchestrator already serves these at `/installer.sh` and `/api/installer/compose` — routing stays unchanged

### Agent distribution documentation

- Update the docs site (Phase 23 getting started guide) to prominently feature the curl one-liner as the primary node installation path:
  ```
  curl -sSL https://<orchestrator>/installer.sh | bash -s -- --token "<JOIN_TOKEN>"
  ```
- Document the `/api/installer/compose?token=...` route which serves a ready-to-run `node-compose.yaml`
- Two install personas: Docker Compose (for users who want control) + curl one-liner bash installer (for easy path)

### Claude's Discretion

- Exact GitHub Actions workflow file names and structure (e.g., `ci.yml`, `release.yml` vs combined)
- Whether to use `docker/metadata-action` for tag generation or manual tag logic
- Job parallelism and dependency graph within workflows
- Exact pytest and vitest invocation flags in CI (verbosity, coverage reporting)
- Whether to add `CODEOWNERS` file in this phase

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `.github/ISSUE_TEMPLATE/` + `.github/pull_request_template.md` — already created in Phase 26; add `workflows/` directory alongside these
- `pyproject.toml` — ready: `axiom-sdk = 1.0.0-alpha`, `axiom-push = "mop_sdk.cli:main"`, setuptools build backend
- `puppeteer/Containerfile.server` — the build target for the orchestrator Docker image
- `puppeteer/Containerfile.node` — exists but NOT published to registry in this phase
- `puppeteer/requirements.txt` — all backend deps; used in CI pip install
- `puppeteer/installer/install_universal.sh`, `install_node.sh`, `install_universal.ps1`, `install_ca.ps1` — existing installer scripts that need Axiom rebranding

### Established Patterns

- No Alembic — CI must NOT attempt DB migrations; schema is `create_all` at startup
- SQLite used for dev/test — backend tests run with SQLite, no Postgres service needed in CI
- `pytest` entrypoint: `cd puppeteer && pytest` (per CLAUDE.md)
- `vitest` entrypoint: `cd puppeteer/dashboard && npm run test` (per CLAUDE.md)
- Secrets are all runtime env vars — no build-time secrets to manage in Dockerfiles

### Integration Points

- `.github/workflows/` — new directory; create `ci.yml` (test pipeline) and `release.yml` (Docker + PyPI)
- `puppeteer/installer/` — rebrand script content (no structural changes)
- `docs/docs/getting-started.md` (or equivalent) — update to feature curl one-liner prominently
- PyPI Trusted Publisher — requires one-time configuration in pypi.org project settings (OIDC setup); document in CONTEXT or plan as a manual prerequisite step

</code_context>

<specifics>
## Specific Ideas

- Node install primary one-liner: `curl -sSL https://<orchestrator>/installer.sh | bash -s -- --token "<JOIN_TOKEN>"` — this already works, just needs to be the hero path in docs
- "1 for people that want control, 2 for easy" — Docker Compose for power users, curl installer for quick start. Both paths documented.
- 1.0.0-alpha is the first real public release — TestPyPI publish validates the package before promoting to PyPI proper

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 27-ci-cd-packaging-distribution*
*Context gathered: 2026-03-17*
