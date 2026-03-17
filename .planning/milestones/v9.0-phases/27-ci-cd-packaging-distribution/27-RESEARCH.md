# Phase 27: CI/CD, Packaging & Distribution - Research

**Researched:** 2026-03-17
**Domain:** GitHub Actions CI/CD, GHCR Docker multi-arch, PyPI Trusted Publisher, installer rebranding
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**CI triggers and scope**
- Triggers: PRs + push to `main`
- Test suites: backend `pytest`, frontend `vitest` (`npm run test`), frontend lint (`npm run lint`), Docker build validation (`docker build` on Containerfile.server — no push)
- Python matrix: 3.10, 3.11, 3.12
- Database in CI: SQLite only — no Postgres service container

**Docker image release**
- Registry: GHCR only — `ghcr.io/axiom-laboratories/axiom`
- CE only — EE not yet implemented
- Trigger: git tag push matching `v*`
- Tags: semver + `latest` (e.g., `1.0.0-alpha` AND `latest`)
- Published: orchestrator only (Containerfile.server) — node image NOT published
- Architectures: `linux/amd64` + `linux/arm64` via QEMU/buildx
- Build caching: GitHub Actions cache (`type=gha`)
- Secrets: runtime-only — no build-time ARG secrets

**PyPI publishing**
- Trigger: same `v*` git tag as Docker release
- Target: TestPyPI first to validate, then real PyPI
- Package: `mop_sdk/` only
- Auth: PyPI Trusted Publisher (OIDC) — no long-lived API tokens
- Version bump: manual edit to `pyproject.toml` before tagging
- Pre-release: publish `1.0.0-alpha` as PEP 440 `1.0.0a1`

**Installer scripts rebranding**
- Rebrand `install_universal.sh`, `install_node.sh`, `install_universal.ps1` — replace "Master of Puppets" / "MoP" with "Axiom" in banners, comments, output strings
- Routing unchanged

**Agent distribution documentation**
- Update getting-started guide to feature curl one-liner as primary path
- Document `/api/installer/compose?token=...` route
- Two personas: Docker Compose (control) + curl one-liner (easy)

### Claude's Discretion

- Exact GitHub Actions workflow file names and structure (`ci.yml`, `release.yml` vs combined)
- Whether to use `docker/metadata-action` for tag generation or manual tag logic
- Job parallelism and dependency graph within workflows
- Exact pytest and vitest invocation flags in CI
- Whether to add `CODEOWNERS` file in this phase

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

This phase automates the build, test, and distribution pipeline for Axiom. The work splits cleanly into four areas: (1) GitHub Actions CI workflow running tests on every PR/push, (2) GitHub Actions release workflow that builds a multi-arch Docker image to GHCR and publishes the `axiom-sdk` Python package to PyPI on every `v*` tag, (3) rebranding three installer scripts from "Master of Puppets" to "Axiom", and (4) updating the getting-started documentation to foreground the curl one-liner install path.

The standard toolchain is well-established and fully supported by GitHub's managed infrastructure. Docker's official action suite (`docker/setup-qemu-action`, `docker/setup-buildx-action`, `docker/build-push-action`, `docker/metadata-action`) handles the GHCR multi-arch release with minimal boilerplate. PyPA's `pypa/gh-action-pypi-publish` combined with PyPI Trusted Publisher eliminates long-lived secrets from the repository. Both patterns have HIGH confidence, verified against current official documentation.

The key coordination concern is that OIDC Trusted Publisher configuration must be performed manually on pypi.org and test.pypi.org before the release workflow can succeed — this is a human prerequisite step, not automatable. A critical CI pitfall exists: `agent_service/security.py` calls `sys.exit(1)` at import time if `API_KEY` is unset, so backend tests in CI require dummy environment variables even though tests mock the actual behavior.

**Primary recommendation:** Two workflow files (`ci.yml` for tests, `release.yml` for distribution) with `docker/metadata-action@v6` for tag generation and `pypa/gh-action-pypi-publish@release/v1` for PyPI via OIDC.

---

## Standard Stack

### Core
| Library / Action | Version | Purpose | Why Standard |
|-----------------|---------|---------|--------------|
| `actions/checkout` | v4 | Checkout repository | Official GitHub action, standard in all workflows |
| `actions/setup-python` | v5 | Install Python for matrix builds | Official GitHub action |
| `actions/setup-node` | v4 | Install Node.js for frontend tests | Official GitHub action |
| `docker/setup-qemu-action` | v3 | QEMU for cross-arch emulation (arm64 on amd64 host) | Docker's official action, required for multi-arch |
| `docker/setup-buildx-action` | v3 | Docker Buildx for multi-platform builds | Required for `linux/amd64,linux/arm64` in a single job |
| `docker/login-action` | v3 | Authenticate to GHCR | Docker's official registry auth action |
| `docker/metadata-action` | v6 | Generate semver tags + OCI labels from git ref | Eliminates manual tag string assembly; handles `latest=auto` |
| `docker/build-push-action` | v6 | Build and push multi-arch images | Full buildx integration, GHA cache support |
| `pypa/gh-action-pypi-publish` | release/v1 | Publish Python distributions to PyPI/TestPyPI | PyPA's blessed action; OIDC Trusted Publisher support built-in |
| `python -m build` | latest | Build wheel + sdist | Standard PEP 517 build frontend |

### Supporting
| Library / Action | Version | Purpose | When to Use |
|-----------------|---------|---------|-------------|
| `actions/upload-artifact` | v4 | Store built Python dists between jobs | Required for build→publish artifact handoff |
| `actions/download-artifact` | v4 | Retrieve dists in publish jobs | Pairs with upload-artifact |
| `actions/cache` | v4 | Cache pip/npm dependencies | Speeds repeated CI runs; `type=gha` for Docker layer caching is handled by `docker/build-push-action` directly |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `docker/metadata-action` for tag generation | Manual tag string construction in `run:` step | metadata-action also emits OCI labels (org.opencontainers.image.*), provenance annotations — manual misses these |
| QEMU single-job multi-arch | Native arm64 runner + manifest merge | Native runners avoid emulation overhead but require two jobs and a merge step; QEMU is simpler for this project's build volume |
| PyPI Trusted Publisher (OIDC) | Long-lived PyPI API token in GitHub Secrets | API tokens are long-lived; OIDC tokens expire per run; Trusted Publisher is the 2024+ recommended approach |

**Installation (no local install needed — all actions are referenced by tag in YAML):**
```bash
# Python build tooling for CI steps
pip install build
```

---

## Architecture Patterns

### Recommended Workflow File Structure
```
.github/
├── workflows/
│   ├── ci.yml          # PRs + push to main: pytest, vitest, lint, docker build validation
│   └── release.yml     # v* tag push: multi-arch Docker to GHCR + PyPI publish
├── ISSUE_TEMPLATE/     # already exists (Phase 26)
└── pull_request_template.md  # already exists (Phase 26)
```

### Pattern 1: CI Workflow (ci.yml)

**What:** Runs backend tests across Python 3.10/3.11/3.12 matrix, frontend tests with vitest, frontend lint, and validates the Docker image builds without pushing.

**When to use:** On all PRs and pushes to `main`.

**Structure:**
```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: pip install -r puppeteer/requirements.txt
        # CRITICAL: security.py calls sys.exit(1) at import if API_KEY is absent.
        # Tests that exercise routes with mocked auth still trigger the import.
        # Set dummy env vars for the test process.
      - run: cd puppeteer && pytest
        env:
          API_KEY: ci-dummy-key
          ENCRYPTION_KEY: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
          DATABASE_URL: sqlite+aiosqlite:///./test.db

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: puppeteer/dashboard/package-lock.json
      - run: cd puppeteer/dashboard && npm ci
      - run: cd puppeteer/dashboard && npm run lint
      - run: cd puppeteer/dashboard && npm run test

  docker-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - name: Validate Docker build (no push)
        uses: docker/build-push-action@v6
        with:
          context: puppeteer
          file: puppeteer/Containerfile.server
          push: false
          platforms: linux/amd64
```

### Pattern 2: Release Workflow (release.yml)

**What:** On `v*` tag, builds multi-arch Docker image and pushes to GHCR; builds Python package and publishes to TestPyPI then PyPI.

**Tag generation with metadata-action:**
```yaml
# Source: https://github.com/docker/metadata-action
- name: Docker meta
  id: meta
  uses: docker/metadata-action@v6
  with:
    images: ghcr.io/axiom-laboratories/axiom
    flavor: |
      latest=auto
    tags: |
      type=semver,pattern={{version}}
      type=semver,pattern={{major}}.{{minor}}
```

`flavor: latest=auto` causes `latest` to be applied automatically when the highest-version semver tag is pushed. For `v1.0.0-alpha`, this generates tags `1.0.0-alpha` and `latest`.

**GHCR login (required permissions):**
```yaml
permissions:
  contents: read
  packages: write

- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.repository_owner }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

**Multi-arch build with GHA cache:**
```yaml
# Source: https://docs.docker.com/build/ci/github-actions/multi-platform/
- uses: docker/setup-qemu-action@v3
- uses: docker/setup-buildx-action@v3
- uses: docker/build-push-action@v6
  with:
    context: puppeteer
    file: puppeteer/Containerfile.server
    platforms: linux/amd64,linux/arm64
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    labels: ${{ steps.meta.outputs.labels }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**PyPI publish job structure (OIDC):**
```yaml
# Source: https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
build:
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - run: pip install build
    - run: python -m build
    - uses: actions/upload-artifact@v4
      with:
        name: python-package-distributions
        path: dist/

publish-to-testpypi:
  needs: [build]
  environment: testpypi
  permissions:
    id-token: write
  steps:
    - uses: actions/download-artifact@v4
      with:
        name: python-package-distributions
        path: dist/
    - uses: pypa/gh-action-pypi-publish@release/v1
      with:
        repository-url: https://test.pypi.org/legacy/

publish-to-pypi:
  needs: [publish-to-testpypi]
  environment: pypi
  permissions:
    id-token: write
  steps:
    - uses: actions/download-artifact@v4
      with:
        name: python-package-distributions
        path: dist/
    - uses: pypa/gh-action-pypi-publish@release/v1
```

### Anti-Patterns to Avoid

- **Putting `id-token: write` at the workflow level:** This grants OIDC token creation to ALL jobs including Docker build jobs. Always scope it to the specific publish job.
- **Using `GITHUB_TOKEN` for PyPI auth:** It won't work — `GITHUB_TOKEN` is only valid for GitHub's own services. PyPI requires its own OIDC exchange.
- **Storing a PyPI API token in GitHub Secrets:** Trusted Publisher is more secure and now the recommended standard.
- **Building Docker image on every PR with push:** No push on PRs — validate builds but never push. Prevents registry pollution and secrets exposure risk.
- **Running vitest with `npm test` (non-CI flag):** Use `npm run test -- --run` (vitest's CI mode) or rely on `npm run test` only if `vitest.config.ts` already uses `passWithNoTests: true` and exits on completion. The current `package.json` has `"test": "vitest"` which runs in watch mode by default. In CI, pass `--run` flag.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Docker image tag generation | String concatenation in `run:` steps | `docker/metadata-action@v6` | Handles semver patterns, `latest=auto`, OCI label schema, pre-release detection |
| Multi-arch Docker build | Separate workflows per arch with manual manifest merge | `docker/build-push-action@v6` + `docker/setup-qemu-action@v3` | Single job handles emulation + manifest list in one step |
| GHCR authentication | Manual `docker login` with PAT | `docker/login-action@v3` + `GITHUB_TOKEN` + `packages: write` | Auto-scoped to repository, rotates per run |
| Python package publishing | Manual `twine upload` with stored credentials | `pypa/gh-action-pypi-publish@release/v1` + OIDC | Trusted Publisher tokens are per-run, zero secrets in repo |
| Python wheel + sdist build | Manual `python setup.py bdist_wheel` | `python -m build` | PEP 517 standard; setuptools build backend already configured in `pyproject.toml` |

**Key insight:** The Docker build + PyPI release stack is so well-standardized that essentially every step has an official action. Manual shell scripting for any of these tasks introduces version-skew risks and misses correctness edge cases (pre-release tag detection, OCI label schema, OIDC token audience selection).

---

## Common Pitfalls

### Pitfall 1: `security.py` calls `sys.exit(1)` at import time when `API_KEY` is missing

**What goes wrong:** `pytest` imports `agent_service` modules during collection. `security.py` line 19 calls `sys.exit(1)` if `API_KEY` is absent from the environment. CI runners have no `.env` file. All backend tests fail immediately at collection with exit code 1.

**Why it happens:** `API_KEY = os.environ["API_KEY"]` raises `KeyError` on a clean runner. The `except KeyError` block calls `sys.exit(1)`.

**How to avoid:** Set dummy environment variables in the CI workflow step:
```yaml
env:
  API_KEY: ci-dummy-key
  ENCRYPTION_KEY: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
  DATABASE_URL: sqlite+aiosqlite:///./test.db
```
This matches the pattern already used by `test_openapi_export.py`'s `DUMMY_ENV` dict.

**Warning signs:** CI pytest job exits with code 1 before any test result appears; no `PASSED`/`FAILED` output.

### Pitfall 2: vitest watch mode in CI

**What goes wrong:** `npm test` in the dashboard runs `vitest` which defaults to watch mode in an interactive terminal context. In CI (non-TTY), vitest detects no TTY and should exit automatically — but versions below 1.0 can hang.

**Why it happens:** `package.json` has `"test": "vitest"` without `--run`. vitest 1.x+ handles CI auto-detection correctly but relying on it is fragile.

**How to avoid:** In CI, invoke as:
```bash
cd puppeteer/dashboard && npx vitest run
```
Or update `package.json` to have a `"test:ci": "vitest run"` script. Check `vitest.config.ts` — the current config uses `jsdom` environment and `globals: true`, which is compatible.

**Warning signs:** Frontend CI job hangs indefinitely without producing output.

### Pitfall 3: PyPI Trusted Publisher not configured before first release tag

**What goes wrong:** The `publish-to-pypi` job fails with a 403 from PyPI OIDC exchange even though `id-token: write` is set. The workflow is correct but PyPI has no matching Trusted Publisher record.

**Why it happens:** Trusted Publisher requires a one-time manual setup at pypi.org → your project → Publishing → Add a new publisher. The configuration binds a specific GitHub org/repo/workflow file name/environment name to the project.

**How to avoid:** This is a **manual prerequisite** before the first `v*` tag push. The plan must include a task documenting:
1. Create project on TestPyPI + configure Trusted Publisher: owner=`axiom-laboratories`, repo=`master_of_puppets` (or actual repo name), workflow=`release.yml`, environment=`testpypi`
2. Create project on PyPI + configure Trusted Publisher with environment=`pypi`
3. Create GitHub environments `testpypi` and `pypi` in repository settings

**Warning signs:** Release workflow OIDC exchange step fails with HTTP 403; PyPI error message references "trusted publisher not found".

### Pitfall 4: `latest=auto` applies to pre-release tags

**What goes wrong:** Pushing `v1.0.0-alpha` (or PEP 440 `v1.0.0a1`) causes `docker/metadata-action` with `flavor: latest=auto` to tag the image as `latest`, which may mislead users who `docker pull ghcr.io/axiom-laboratories/axiom:latest`.

**Why it happens:** `latest=auto` adds `latest` to any semver tag that is the highest version seen — pre-releases included when no stable release exists yet.

**How to avoid:** For the first release (alpha only), this behavior is acceptable — there is no stable release yet and `latest` pointing to alpha is expected. When a stable release exists alongside pre-releases, switch `flavor` to `latest=false` and add it only on non-prerelease tags:
```yaml
tags: |
  type=semver,pattern={{version}}
  type=raw,value=latest,enable=${{ !contains(github.ref, 'alpha') && !contains(github.ref, 'beta') }}
```
For now (alpha-only), accept `latest=auto`.

### Pitfall 5: `linux/arm64` QEMU build is slow

**What goes wrong:** Multi-arch builds with QEMU emulation can take 15-30 minutes for Python Alpine images that compile native extensions (e.g., `cryptography`, `psutil`).

**Why it happens:** QEMU emulates the arm64 CPU entirely in software — compile-intensive C extensions like `cryptography` run at 10-20x slower than native.

**How to avoid:** Use `cache-from: type=gha` + `cache-to: type=gha,mode=max` to avoid rebuilding unchanged layers. The Containerfile.server copies dependencies before source code, so `pip install` layer is cached unless `requirements.txt` changes. Ensure `requirements.txt` is copied before `COPY agent_service/` in the Containerfile to maximize layer reuse.

**Warning signs:** Release workflow takes >20 minutes; GHA cache hit rate is low.

---

## Code Examples

Verified patterns from official sources:

### Full ci.yml skeleton
```yaml
# Source: https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-python
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: pip install -r puppeteer/requirements.txt
      - run: cd puppeteer && pytest -v
        env:
          API_KEY: ci-dummy-key
          ENCRYPTION_KEY: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
          DATABASE_URL: sqlite+aiosqlite:///./test.db

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: puppeteer/dashboard/package-lock.json
      - run: cd puppeteer/dashboard && npm ci
      - run: cd puppeteer/dashboard && npm run lint

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: puppeteer/dashboard/package-lock.json
      - run: cd puppeteer/dashboard && npm ci
      - run: cd puppeteer/dashboard && npx vitest run

  docker-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v6
        with:
          context: puppeteer
          file: puppeteer/Containerfile.server
          push: false
          platforms: linux/amd64
```

### Full release.yml skeleton
```yaml
# Source: https://docs.docker.com/build/ci/github-actions/multi-platform/
# Source: https://docs.pypi.org/trusted-publishers/using-a-publisher/
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: python-package-distributions
          path: dist/

  publish-testpypi:
    needs: [build-python]
    runs-on: ubuntu-latest
    environment:
      name: testpypi
      url: https://test.pypi.org/p/axiom-sdk
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: python-package-distributions
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/

  publish-pypi:
    needs: [publish-testpypi]
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/axiom-sdk
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: python-package-distributions
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1

  docker-release:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-qemu-action@v3
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.repository_owner }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: meta
        uses: docker/metadata-action@v6
        with:
          images: ghcr.io/axiom-laboratories/axiom
          flavor: |
            latest=auto
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
      - uses: docker/build-push-action@v6
        with:
          context: puppeteer
          file: puppeteer/Containerfile.server
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Installer script rebranding pattern

The three files with "Master of Puppets" / "MoP" occurrences requiring change:

| File | Line(s) | Current | Replace with |
|------|---------|---------|--------------|
| `install_universal.sh` | Line 2 | `# Master of Puppets - Universal Installer (v1.0) - Linux/macOS` | `# Axiom - Universal Installer (v1.0) - Linux/macOS` |
| `install_universal.sh` | Line 47 | `mop-root.crt` (filename reference) | `axiom-root.crt` |
| `install_universal.sh` | Line 50 | `mop-root.crt` (filename reference) | `axiom-root.crt` |
| `install_node.sh` | Line 2 | `# Master of Puppets - Linux Node Installer` | `# Axiom - Linux Node Installer` |
| `install_universal.ps1` | Line 1 | `# Master of Puppets - Universal Installer (v1.0)` | `# Axiom - Universal Installer (v1.0)` |

Note: `install_ca.ps1` also matches the grep — verify its content and rebrand if it contains user-visible MoP strings.

### Docs update pattern — enroll-node.md

The current `enroll-node.md` only documents the Docker Compose path (Step 3: Create the node compose file). Add a new section at the top presenting two install methods:

**Easy path (curl one-liner):**
```bash
curl -sSL https://<your-orchestrator>/installer.sh | bash -s -- --token "<JOIN_TOKEN>"
```

**Power-user path (Docker Compose):** existing Steps 3-5.

The `/api/installer/compose?token=...` endpoint generates a ready-to-run `node-compose.yaml` — document it as the behind-the-scenes mechanism that the curl installer uses, and make it available for users who want to review or customise the compose file before running it.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PyPI API tokens (long-lived, stored in GitHub Secrets) | OIDC Trusted Publisher (per-run tokens, no secret storage) | 2023 — PyPI Trusted Publisher GA | Eliminates long-lived credential compromise risk |
| Manual `docker buildx build --platform` in shell | `docker/build-push-action@v6` with `platforms:` | 2022-2024 | Single-step multi-arch + cache + push |
| `docker/metadata-action@v4/v5` | `docker/metadata-action@v6` | 2024 | v6 adds attestation support, updated OCI label schema |
| `python setup.py bdist_wheel` | `python -m build` | 2021 (PEP 517) | Backend-agnostic; setuptools build backend already declared in `pyproject.toml` |

**Deprecated/outdated:**
- `actions/upload-artifact@v3` and `actions/download-artifact@v3`: Use v4. v3 reaches end-of-support in 2024.
- `docker/build-push-action@v4/v5`: Use v6. Action versions below v6 lack full provenance attestation support.
- Storing a `PYPI_API_TOKEN` in GitHub Secrets: Superseded by Trusted Publisher for all new projects.

---

## Open Questions

1. **Actual GitHub organization name for GHCR image path**
   - What we know: CONTEXT.md specifies `ghcr.io/axiom-laboratories/axiom`
   - What's unclear: Whether the GitHub organization `axiom-laboratories` exists and the repository is already transferred to it, or whether `axiom-laboratories` is aspirational. The release workflow image path must match the org that owns the repository.
   - Recommendation: Plan should include a verification step — if org doesn't exist, use `ghcr.io/${{ github.repository_owner }}/axiom` as the fallback which resolves dynamically.

2. **`install_ca.ps1` branding scope**
   - What we know: File matches grep for "Master of Puppets" but CONTEXT.md only explicitly names `install_universal.sh`, `install_node.sh`, `install_universal.ps1`
   - What's unclear: Whether `install_ca.ps1` has user-visible MoP branding that should be rebrandedhttp
   - Recommendation: Read `install_ca.ps1` in the plan task and rebrand if it has user-visible strings. Low-risk addition to the installer task.

3. **vitest CI invocation**
   - What we know: `package.json` has `"test": "vitest"` (watch mode default). `vitest.config.ts` has no explicit `passWithNoTests`.
   - What's unclear: Whether the current vitest version auto-detects CI=true and exits. vitest 1.x does CI detection but watch mode in GitHub Actions (non-TTY) may still hang on older versions.
   - Recommendation: Use `npx vitest run` explicitly in CI rather than `npm run test` to guarantee non-watch execution. Can also be `npm run test -- --run` if the `--` separator is preferred.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (backend) | pytest (version in requirements.txt) |
| Framework (frontend) | vitest (see vitest.config.ts) |
| Config file (backend) | `pyproject.toml` — `[tool.pytest.ini_options]` with `pythonpath = ["puppeteer"]`, `asyncio_mode = "auto"` |
| Config file (frontend) | `puppeteer/dashboard/vitest.config.ts` |
| Backend quick run | `cd puppeteer && pytest -x` |
| Backend full suite | `cd puppeteer && pytest` |
| Frontend test run | `cd puppeteer/dashboard && npx vitest run` |

### Phase Requirements → Test Map

This phase has no formal requirement IDs. Validation is behavioral:

| Behavior | Test Type | Automated Command |
|----------|-----------|-------------------|
| CI workflow syntax is valid YAML | smoke | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` |
| Release workflow syntax is valid YAML | smoke | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"` |
| Backend tests pass on Python 3.12 with dummy env vars | unit/integration | `API_KEY=ci-dummy-key ENCRYPTION_KEY=AAAA... cd puppeteer && pytest` |
| Frontend tests pass | unit | `cd puppeteer/dashboard && npx vitest run` |
| Installer scripts contain no "Master of Puppets" / "MoP" strings | content | `grep -r "Master of Puppets\|MoP" puppeteer/installer/` (should return empty) |
| `python -m build` produces wheel + sdist | smoke | `pip install build && python -m build && ls dist/` |

### Wave 0 Gaps

- [ ] `pip install pyyaml` in CI test environment — needed for YAML syntax validation smoke test (optional, low priority)
- [ ] No new test files needed — existing `puppeteer/tests/` and `puppeteer/dashboard/src/views/__tests__/` cover the application; this phase only adds workflow files and docs

None — existing test infrastructure covers all application behavior. Workflow files are infrastructure-as-code, validated by GitHub Actions runner at execution time.

---

## Sources

### Primary (HIGH confidence)
- [Docker multi-platform GitHub Actions official docs](https://docs.docker.com/build/ci/github-actions/multi-platform/) — QEMU + buildx + GHA cache pattern
- [docker/metadata-action GitHub](https://github.com/docker/metadata-action) — semver tag + flavor configuration, current version v6
- [PyPI Trusted Publisher docs](https://docs.pypi.org/trusted-publishers/using-a-publisher/) — OIDC workflow requirements
- [Python Packaging User Guide — GitHub Actions publishing](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) — build + TestPyPI + PyPI job structure
- [GitHub Docs — GHCR permissions](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) — `packages: write`, `GITHUB_TOKEN` usage
- [GitHub Docs — Building and testing Python](https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing/building-and-testing-python) — matrix strategy pattern

### Secondary (MEDIUM confidence)
- `puppeteer/tests/test_openapi_export.py` — `DUMMY_ENV` pattern confirms `API_KEY` + `ENCRYPTION_KEY` + `DATABASE_URL` are the required dummy vars for test environment
- `puppeteer/agent_service/security.py` line 19 — direct code inspection confirms `sys.exit(1)` at import on missing `API_KEY`
- `puppeteer/installer/install_universal.sh` + `install_node.sh` + `install_universal.ps1` — direct inspection of branding occurrences

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack (actions, versions): HIGH — verified against official Docker, PyPI, and GitHub documentation
- Architecture (workflow structure): HIGH — canonical patterns from official guides
- Pitfalls: HIGH (sys.exit import trap) / MEDIUM (vitest watch mode) — confirmed by direct code inspection and known CI behavior
- Installer rebranding scope: HIGH — confirmed by direct grep of actual files

**Research date:** 2026-03-17
**Valid until:** 2026-06-17 (actions semver versions change; re-verify docker/build-push-action and docker/metadata-action major versions before implementing)
