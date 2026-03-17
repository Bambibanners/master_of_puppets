# Phase 21: API Reference + Dashboard Integration - Research

**Researched:** 2026-03-16
**Domain:** FastAPI OpenAPI schema export, mkdocs-swagger-ui-tag plugin, React route removal, sidebar external link
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| APIREF-01 | API reference rendered in MkDocs from a static `openapi.json` snapshot | mkdocs-swagger-ui-tag plugin reads a local file placed in `docs/docs/api-reference/`; no runtime server needed |
| APIREF-02 | `openapi.json` generated from FastAPI at container build time (no running server required) | `app.openapi()` import in Dockerfile builder stage via `scripts/export_openapi.py`; SQLAlchemy creates async engine at module import but does not connect until a coroutine runs |
| APIREF-03 | API reference displays all endpoints grouped by tag with request/response schemas | FastAPI routes currently only tagged for Foundry, Smelter Registry, Headless Automation — all others fall into "default"; tags must be added before export for useful grouping |
| DASH-01 | Sidebar "Docs" entry opens the docs site in a new tab | Replace `NavItem` (which uses `NavLink` + React Router) with a plain `<a>` tag pointing to `/docs/` with `target="_blank"` |
| DASH-02 | `Docs.tsx` route and in-app markdown renderer are removed | Delete `Docs.tsx`, remove import and `<Route path="docs">` from `AppRoutes.tsx`, remove `UserGuide.md` import if no other consumer |
</phase_requirements>

---

## Summary

Phase 21 has two independent tracks. Track A is the OpenAPI export pipeline: a `scripts/export_openapi.py` script imports the FastAPI `app` object and calls `app.openapi()` — no running server needed — writes `openapi.json` into the docs source tree, and the mkdocs-swagger-ui-tag plugin renders it using bundled Swagger UI assets (no CDN). Track B is a small React cleanup: remove the `Docs.tsx` view and its route, and replace the sidebar nav item with an `<a>` tag that opens `/docs/` in a new tab.

The most important pre-work for APIREF-03 is tagging all FastAPI routes. Currently only 22 routes across three tags exist (`Foundry`, `Smelter Registry`, `Headless Automation`); the remaining ~120 routes fall under `default`. Without adding tags, the Swagger UI will render a single enormous "default" section with no grouping. Adding tags is low-risk (decorators only, no logic change) and must happen before the export script runs.

The SQLAlchemy concern flagged in STATE.md is real but manageable: `db.py` calls `create_async_engine(DATABASE_URL)` at module level. This means importing `main.py` will create the engine object. The engine object creation does not open a connection — connections are only made when a coroutine actually runs. The `app.openapi()` call is synchronous and does not execute any route handlers or coroutines, so no actual DB connection is made. However, the engine reads `DATABASE_URL` at import time, so a dummy value must be set to avoid an `asyncpg` connection-string validation error. Setting `DATABASE_URL=sqlite+aiosqlite:///./dummy.db` in the builder stage is sufficient.

**Primary recommendation:** Add route tags to all un-tagged routes in `main.py` first, then export `openapi.json`, then wire in the MkDocs plugin — all as a single atomic task to avoid a `--strict` build gap.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mkdocs-swagger-ui-tag | 0.8.0 (latest, released 2026-02-22) | Embeds Swagger UI in MkDocs pages using local assets | Bundles all Swagger UI JS/CSS locally — zero CDN requests; designed for intranet/air-gap deployments; supports local OpenAPI file reference |
| mkdocs-material | 9.7.5 (already pinned) | MkDocs theme | Already in `docs/requirements.txt` — no change needed |
| FastAPI | already in stack | Provides `app.openapi()` for schema export | Built-in — no new dependency |
| python:3.12-slim | already in Dockerfile builder stage | Runs `export_openapi.py` | Already the builder base image |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uvicorn | already in `requirements.txt` | `uvicorn.importer.import_from_string` for clean app import | Used in export script to load the app cleanly from module path |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| mkdocs-swagger-ui-tag | mkdocs-render-swagger-plugin (bharel) | Both work; blueswen's plugin (0.8.0) is more actively maintained, has better offline story, and supports dark mode sync with Material theme |
| `app.openapi()` script | FastAPI `--reload` + `curl /openapi.json` | Requires a running server + env vars + wait for startup; much more complex in a builder stage with no DB |
| Docker builder stage script | Pre-committed `openapi.json` | Committed file goes stale; violates APIREF-02 (must be auto-generated at build time) |

**Installation addition to `docs/requirements.txt`:**
```
mkdocs-material==9.7.5
mkdocs-swagger-ui-tag==0.8.0
```

**Export script dependencies** — add to `puppeteer/requirements.txt` if not present (already in stack):
```
uvicorn  # already present — used for import_from_string
```

---

## Architecture Patterns

### Recommended File Structure Changes

```
docs/
├── mkdocs.yml               # add swagger-ui-tag plugin
├── requirements.txt         # add mkdocs-swagger-ui-tag==0.8.0
├── Dockerfile               # add builder stage step to copy + run export script
├── nginx.conf               # unchanged
└── docs/
    ├── index.md             # unchanged
    └── api-reference/
        ├── index.md         # swagger-ui tag pointing to openapi.json
        └── openapi.json     # generated by export_openapi.py during Docker build

puppeteer/
├── agent_service/
│   └── main.py              # add tags to all un-tagged routes
└── scripts/
    └── export_openapi.py    # new — exports openapi.json without running server

puppeteer/dashboard/src/
├── AppRoutes.tsx            # remove <Route path="docs"> and Docs import
├── layouts/MainLayout.tsx   # replace NavItem for Docs with <a> external link
├── views/
│   └── Docs.tsx             # DELETE
└── assets/
    └── UserGuide.md         # DELETE (no other consumers)
```

### Pattern 1: export_openapi.py — Schema Export Without a Running Server

**What:** Import the FastAPI app object, call `app.openapi()`, write JSON to a file. No HTTP server. No DB connection. Synchronous.

**When to use:** In the Docker builder stage, before `mkdocs build`.

**Critical detail:** `db.py` calls `create_async_engine(DATABASE_URL)` at module import. The engine object is created but no connection is opened until a coroutine runs. `app.openapi()` is synchronous and never runs route handlers — so no DB connection is made. However, `asyncpg` validates the connection string at engine creation on some versions. Use `sqlite+aiosqlite:///./dummy.db` as `DATABASE_URL` to avoid this.

```python
# Source: FastAPI discussions #7445, #1490
#!/usr/bin/env python3
"""
Export FastAPI OpenAPI schema to a JSON file without running a server.
Run from puppeteer/ directory:
  DATABASE_URL=sqlite+aiosqlite:///./dummy.db \
  ENCRYPTION_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
  python scripts/export_openapi.py ../docs/docs/api-reference/openapi.json
"""
import sys
import json
import os

# Ensure puppeteer/ is on the path so agent_service package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_service.main import app

schema = app.openapi()

out = sys.argv[1] if len(sys.argv) > 1 else "openapi.json"
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
with open(out, "w") as f:
    json.dump(schema, f, indent=2)
print(f"Wrote {len(json.dumps(schema))} bytes to {out}")
```

### Pattern 2: Dockerfile Builder Stage Integration

**What:** Add export script execution between `pip install` (which installs the FastAPI app's deps) and `mkdocs build`. The `openapi.json` is generated into the MkDocs source tree so `mkdocs build` picks it up and embeds it in the static site.

**Key ordering:** Export script must run AFTER pip install (deps needed) and BEFORE mkdocs build (schema must exist when MkDocs processes the swagger-ui tag).

```dockerfile
# Source: existing docs/Dockerfile pattern + export_openapi.py pattern
FROM python:3.12-slim AS builder
WORKDIR /docs

# Install MkDocs deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install FastAPI app deps (for export script)
COPY ../puppeteer/requirements.txt /tmp/app-requirements.txt
RUN pip install --no-cache-dir -r /tmp/app-requirements.txt

# Copy MkDocs source + export script
COPY . .
COPY ../puppeteer/scripts/export_openapi.py /tmp/export_openapi.py
COPY ../puppeteer/agent_service /tmp/agent_service

# Generate openapi.json from FastAPI app (no running server)
RUN DATABASE_URL=sqlite+aiosqlite:///./dummy.db \
    ENCRYPTION_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
    python /tmp/export_openapi.py docs/api-reference/openapi.json

# Build MkDocs site (strict — fails on any warning)
RUN mkdocs build --strict

FROM nginx:alpine
COPY --from=builder /docs/site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Note on build context:** The current `compose.server.yaml` sets `context: ../docs`. To `COPY` from `../puppeteer/`, the build context must be expanded to the repo root. Options:
1. Change `context: .` (repo root) and `dockerfile: docs/Dockerfile` — requires updating compose.server.yaml
2. Keep `context: ../docs` and copy the export script + agent_service into `docs/` at build time via a Makefile/CI step — adds complexity
3. **Recommended:** Change build context to repo root in compose.server.yaml

```yaml
# compose.server.yaml update
docs:
  image: localhost/master-of-puppets-docs:v1
  build:
    context: ..           # repo root (was: ../docs)
    dockerfile: docs/Dockerfile
  restart: always
```

### Pattern 3: mkdocs.yml Plugin Configuration

**What:** Add `swagger-ui-tag` to the plugins list. Add `api-reference/index.md` to nav (or leave nav-less for now — `--strict` will warn about an undeclared page).

```yaml
# Source: blueswen.github.io/mkdocs-swagger-ui-tag
site_name: Master of Puppets
site_url: https://dev.master-of-puppets.work/docs/
theme:
  name: material
  palette:
    scheme: slate
    primary: indigo
    accent: indigo
plugins:
  - search
  - privacy
  - offline
  - swagger-ui-tag
```

**Note:** The `privacy` plugin will attempt to download external assets referenced by the Swagger UI plugin. Since `mkdocs-swagger-ui-tag` bundles all its assets locally, there should be no external requests introduced by the plugin itself. However, if `openapi.json` contains external `$ref` URLs, those would not be downloaded (Swagger UI resolves them at runtime). This is not an issue for this project — the FastAPI schema is fully self-contained.

### Pattern 4: api-reference/index.md — Swagger UI Page

**What:** A MkDocs page that uses the `swagger-ui` custom HTML tag introduced by the plugin. The `src` attribute points to `openapi.json` in the same directory.

```markdown
# API Reference

<swagger-ui src="openapi.json" validatorUrl="none"/>
```

**`validatorUrl="none"`** disables the online Swagger validator (which would make a network request to `validator.swagger.io`). Required for air-gap compliance.

### Pattern 5: Sidebar External Link in MainLayout.tsx

**What:** Replace the `NavItem` component (which uses React Router `NavLink`) with a plain `<a>` element for the Docs entry. The existing `NavItem` component wires into React Router — it cannot open external URLs in a new tab.

**Pattern for the external link item:**
```tsx
// Source: project's existing NavItem pattern + standard HTML anchor
<a
  href="/docs/"
  target="_blank"
  rel="noopener noreferrer"
  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-zinc-800 hover:text-white text-zinc-400"
  aria-label="Documentation"
>
  <BookOpen className="h-4 w-4 shrink-0" />
  <span>Docs</span>
</a>
```

Import `BookOpen` from `lucide-react` (already a project dependency). The class string matches the inactive state of `NavItem` exactly — it will never receive the `isActive` highlight since it's not a React Router route.

**Place in SidebarContent:** Add under the System section (or create a new section). The current sidebar has no Docs entry — it was accessible via route but not in the sidebar nav. DASH-01 requires it to be visible.

### Pattern 6: AppRoutes.tsx and Docs.tsx Removal

**What:** Three deletions and one file removal.

1. Remove `const Docs = lazy(() => import('./views/Docs'))` from `AppRoutes.tsx`
2. Remove `<Route path="docs" element={<Docs />} />` from `AppRoutes.tsx`
3. Delete `puppeteer/dashboard/src/views/Docs.tsx`
4. Delete `puppeteer/dashboard/src/assets/UserGuide.md` (only consumer is `Docs.tsx`)

**DASH-02 note:** "navigating to it redirects or shows 404" — React Router with no matching route renders nothing (or the 404 fallback if one exists). The current `AppRoutes.tsx` has no explicit 404 route. Removing the route means `/docs` within the React app will fall through to the top-level `<Route path="/">` which renders `<MainLayout>` with an empty `<Outlet>`. This is acceptable — or a `<Route path="*">` redirect to `/` can be added if preferred. The planner should decide; the success criteria says "redirects or shows 404".

### Anti-Patterns to Avoid

- **Committing openapi.json to the repo:** Stale immediately. Always generate at build time.
- **Using `handle_path` in Caddy for API reference assets:** Already correctly set to `handle` in Phase 20 — do not change.
- **Importing only `main.py` without env vars:** `db.py` creates async engine with `DATABASE_URL` at module level. Missing `DATABASE_URL` → defaults to SQLite which is fine. Missing `ENCRYPTION_KEY` → `security.py` imports `cipher_suite = Fernet(ENCRYPTION_KEY)` at module level → this WILL raise an error if `ENCRYPTION_KEY` is unset or invalid. Must set a dummy 32-byte base64 Fernet key.
- **Forgetting `validatorUrl="none"`:** Without this, Swagger UI makes a POST to `validator.swagger.io` for each schema load — breaks air-gap requirement.
- **Using `NavLink` for the docs sidebar entry:** React Router `NavLink` only handles internal routes. Use plain `<a>` with `target="_blank"`.
- **Leaving tags off routes:** Without tags, all ~120 untagged routes render in a single "default" section in Swagger UI — not useful. Tag them before running the export.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Swagger UI embedding | Custom JS/HTML in markdown | `mkdocs-swagger-ui-tag` plugin | Plugin handles Swagger UI version pinning, asset bundling, dark mode, offline mode |
| OpenAPI export from running server | `curl localhost:8001/openapi.json` in Docker | `app.openapi()` direct import | No server process needed; no port conflicts; no startup wait; works in isolated builder stage |
| CDN asset download in Dockerfile | `RUN wget https://unpkg.com/swagger-ui-dist/...` | `mkdocs-swagger-ui-tag` bundles assets | Plugin already bundles pinned Swagger UI assets — no manual download needed |

**Key insight:** `app.openapi()` is a pure Python function call — it introspects route decorators and Pydantic models with no I/O. The only I/O risk is at module import time (engine creation). A single dummy env var covers this.

---

## Common Pitfalls

### Pitfall 1: ENCRYPTION_KEY causes import failure

**What goes wrong:** `export_openapi.py` fails with `ValueError: Fernet key must be 32 url-safe base64-encoded bytes` or similar when importing `agent_service.main`.

**Why it happens:** `puppeteer/agent_service/security.py` calls `Fernet(ENCRYPTION_KEY)` at module level — it runs at import time, not at request time. If `ENCRYPTION_KEY` is absent or not a valid Fernet key (32 bytes, url-safe base64), the import fails.

**How to avoid:** Set a dummy valid Fernet key in the builder stage:
```
ENCRYPTION_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
```
(That is `b'\x00' * 32` base64-encoded — valid Fernet format, harmless.)

**Warning signs:** `ImportError` or `ValueError` when running `export_openapi.py` in the Docker builder stage.

### Pitfall 2: Build context must cover both `docs/` and `puppeteer/`

**What goes wrong:** `COPY ../puppeteer/agent_service /tmp/agent_service` fails with "context does not exist" because the Docker build context is `../docs` (current setting).

**Why it happens:** Docker COPY paths are relative to the build context, not the Dockerfile location. With `context: ../docs`, only files inside `docs/` are accessible to the Dockerfile.

**How to avoid:** Change build context to repo root in `compose.server.yaml` and update Dockerfile paths accordingly.

**Warning signs:** `COPY` instruction fails during `docker compose build docs` with a path-not-found error.

### Pitfall 3: `--strict` fails because openapi.json is referenced but nav is not updated

**What goes wrong:** `mkdocs build --strict` fails with a warning about `api-reference/index.md` not being in `nav`.

**Why it happens:** When MkDocs finds a page in the docs directory that isn't declared in `nav`, it emits a warning. With `--strict`, warnings are fatal.

**How to avoid:** Either (a) leave `nav:` undefined in `mkdocs.yml` entirely (MkDocs auto-discovers all pages, no nav warning), or (b) add the page to `nav`. Since Phase 23 locks nav structure, option (a) is correct for now — do not define `nav:` yet.

**Warning signs:** Docker build fails with "Documentation file 'api-reference/index.md' is not in the nav".

### Pitfall 4: Swagger UI validator makes network requests

**What goes wrong:** The API reference page makes a POST request to `validator.swagger.io` on each load, violating the air-gap requirement (INFRA-06 from Phase 20).

**Why it happens:** Swagger UI's default configuration validates the spec against an online validator service.

**How to avoid:** Set `validatorUrl="none"` on the `<swagger-ui>` tag in `api-reference/index.md`.

**Warning signs:** Network tab shows POST requests to `validator.swagger.io` when viewing the API reference.

### Pitfall 5: `offline` plugin + `use_directory_urls: false` affects Swagger UI src path

**What goes wrong:** The `src="openapi.json"` in `api-reference/index.md` resolves correctly when `use_directory_urls: true` (page is at `api-reference/index.html`, same directory as `openapi.json`) but may need adjustment if directory URL behavior changes.

**Why it happens:** The `offline` plugin sets `use_directory_urls: false` — pages become `api-reference.html` rather than `api-reference/index.html`. The `openapi.json` file is in `api-reference/`, so the relative path from `api-reference.html` would need to be `api-reference/openapi.json`.

**How to avoid:** Test the rendered path. If `use_directory_urls: false` is active, use `src="api-reference/openapi.json"` in `index.md`, or copy `openapi.json` to the docs root and use `src="openapi.json"` from a page at the root level.

**Recommendation:** Keep `openapi.json` in `docs/docs/api-reference/` and `api-reference/index.md` using `src="openapi.json"`. With `offline` plugin active (`use_directory_urls: false`), verify the path resolves. MkDocs Material copies static files maintaining their paths relative to docs root.

**Warning signs:** Swagger UI renders with "Failed to load API definition" or a 404 for `openapi.json`.

### Pitfall 6: Route tags — untagged routes create unusable Swagger UI

**What goes wrong:** Swagger UI renders a single "default" section with 120+ endpoints — no grouping, no navigation.

**Why it happens:** FastAPI only defines tags for 22 routes in `main.py`. All others have no `tags=` parameter and appear under "default".

**How to avoid:** Before running the export script, add `tags=["<group>"]` to all un-tagged routes. Suggested tag groups based on route path patterns:
- `/auth/*` → `"Authentication"`
- `/admin/users`, `/admin/roles` → `"User Management"`
- `/admin/service-principals` → `"Service Principals"` (or merge with User Management)
- `/admin/audit-log` → `"Audit Log"`
- `/jobs`, `/jobs/*` → `"Jobs"`
- `/job-definitions`, `/jobs/definitions` → `"Job Definitions"`
- `/nodes`, `/nodes/*` → `"Nodes"`
- `/signatures` → `"Signatures"`
- `/system/*` → `"System"`
- `/webhooks` → `"Webhooks"`
- `/api/executions` → `"Execution Records"`
- `/api/alerts` → `"Alerts"`
- Other `/admin/*` → `"Admin"`

**Warning signs:** Swagger UI shows only a "default" section.

---

## Code Examples

### Export Script (Minimal, Verified Pattern)

```python
# Source: FastAPI discussions #7445, #12216 — app.openapi() approach
#!/usr/bin/env python3
import sys, json, os

# puppeteer/ must be on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_service.main import app  # triggers db.py engine creation at import

schema = app.openapi()
out = sys.argv[1] if len(sys.argv) > 1 else "openapi.json"
os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
with open(out, "w") as f:
    json.dump(schema, f, indent=2)
print(f"openapi.json written: {len(schema['paths'])} paths")
```

### mkdocs.yml with swagger-ui-tag plugin

```yaml
# Source: blueswen.github.io/mkdocs-swagger-ui-tag
site_name: Master of Puppets
site_url: https://dev.master-of-puppets.work/docs/
theme:
  name: material
  palette:
    scheme: slate
    primary: indigo
    accent: indigo
plugins:
  - search
  - privacy
  - offline
  - swagger-ui-tag
```

### api-reference/index.md

```markdown
# API Reference

Full REST API for Master of Puppets. All endpoints require JWT authentication
except where noted.

<swagger-ui src="openapi.json" validatorUrl="none"/>
```

### Dockerfile builder stage additions

```dockerfile
# After pip install of mkdocs deps, before mkdocs build:
COPY puppeteer/requirements.txt /tmp/app-requirements.txt
RUN pip install --no-cache-dir -r /tmp/app-requirements.txt

COPY puppeteer/agent_service /tmp/agent_service
COPY puppeteer/scripts/export_openapi.py /tmp/export_openapi.py

RUN DATABASE_URL=sqlite+aiosqlite:///./dummy.db \
    ENCRYPTION_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= \
    python /tmp/export_openapi.py docs/api-reference/openapi.json
```

### External Docs link in MainLayout.tsx sidebar

```tsx
// Source: project's existing NavItem CSS class pattern
// Replace in SidebarContent nav, add under System section or end of nav
import { BookOpen } from 'lucide-react';

<a
  href="/docs/"
  target="_blank"
  rel="noopener noreferrer"
  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-zinc-800 hover:text-white text-zinc-400"
  aria-label="Documentation"
>
  <BookOpen className="h-4 w-4 shrink-0" />
  <span>Docs</span>
</a>
```

### AppRoutes.tsx — what to remove

```tsx
// REMOVE these lines:
const Docs = lazy(() => import('./views/Docs'));
// ...
<Route path="docs" element={<Docs />} />
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Swagger CDN from unpkg.com | mkdocs-swagger-ui-tag bundles assets locally | Plugin's founding purpose | Zero CDN requests for API reference |
| FastAPI built-in `/docs` (Swagger UI) | Static snapshot in MkDocs | This phase | Versioned, offline, consistent with docs site |
| In-app markdown renderer (Docs.tsx) | External docs site at /docs/ | This phase | Consolidates documentation in one place |

**Deprecated/outdated:**
- `puppeteer/dashboard/src/views/Docs.tsx`: to be deleted in Plan 21-02
- `puppeteer/dashboard/src/assets/UserGuide.md`: to be deleted with Docs.tsx (only consumer)

---

## Open Questions

1. **Route tagging scope for APIREF-03**
   - What we know: 22 of ~144 routes have tags; the rest are "default"
   - What's unclear: Whether the planner wants Plan 21-01 to include adding tags to all routes, or whether APIREF-03 is satisfied with the current grouping (three tagged groups + one large "default")
   - Recommendation: Include route tagging as a task in Plan 21-01 before the export runs. The success criterion "grouped by tag" implies meaningful groups, not just "default". Suggest the tag groups listed in Pitfall 6.

2. **Dummy ENCRYPTION_KEY format**
   - What we know: `security.py` calls `Fernet(ENCRYPTION_KEY)` at import; Fernet requires 32-byte url-safe base64 value
   - What's unclear: Whether other imports in `main.py` have additional env var requirements beyond `DATABASE_URL` and `ENCRYPTION_KEY`
   - Recommendation: STATE.md already flags this: "Test export_openapi.py locally against a clean Python env as first task — SQLAlchemy async engine may require dummy env vars." Make Task 1 of Plan 21-01 a local verification of the export script with the two dummy vars.

3. **`/docs` route 404 vs redirect (DASH-02)**
   - What we know: Removing `<Route path="docs">` leaves React Router with no match for `/docs` within the React app (Note: this is the React-internal `/docs` route, distinct from the `/docs/` Caddy route serving MkDocs)
   - What's unclear: Whether a catch-all redirect to `/` should be added
   - Recommendation: Add a `<Route path="*" element={<Navigate to="/" replace />} />` catch-all in AppRoutes.tsx for clean UX. This satisfies "redirects" in the success criterion.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (backend) + vitest (frontend) |
| Config file | `puppeteer/pytest.ini` / `puppeteer/dashboard/vitest.config.ts` |
| Quick run command | `docker compose build docs` (validates full pipeline) |
| Full suite command | `cd puppeteer && pytest` + `cd puppeteer/dashboard && npm run test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| APIREF-01 | openapi.json embedded in built MkDocs site | build smoke | `docker compose build docs && docker run --rm localhost/master-of-puppets-docs:v1 find /usr/share/nginx/html -name "openapi.json"` | Wave 0 (generated) |
| APIREF-02 | Export script runs without a server | unit | `DATABASE_URL=sqlite+aiosqlite:///./dummy.db ENCRYPTION_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= python puppeteer/scripts/export_openapi.py /tmp/out.json && test -f /tmp/out.json` | ❌ Wave 0 — create script |
| APIREF-03 | Paths grouped by tag in schema | unit | `python -c "import json; s=json.load(open('/tmp/out.json')); assert any(t!='default' for p in s['paths'].values() for m in p.values() for t in m.get('tags',['default'])), 'No non-default tags'"` | ❌ Wave 0 — requires route tagging |
| DASH-01 | Sidebar Docs link opens /docs/ | manual | Browser test: click Docs link, verify new tab opens at /docs/ | Manual only — requires browser |
| DASH-02 | /docs React route removed | unit (vitest) | `npm run test -- --run` (AppRoutes tests if they exist; otherwise build verification) | ❌ Wave 0 — no existing AppRoutes test |

### Sampling Rate

- **Per task commit:** `docker compose build docs` for Plan 21-01 tasks; `cd puppeteer/dashboard && npm run build` for Plan 21-02 tasks
- **Per wave merge:** `docker compose build docs && docker compose up -d docs` then verify `/docs/api-reference/` loads in browser
- **Phase gate:** Full suite green + manual browser verification of API reference + new-tab docs link before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `puppeteer/scripts/export_openapi.py` — core export script (create in Task 1 of Plan 21-01)
- [ ] `docs/docs/api-reference/index.md` — Swagger UI page (create in Plan 21-01)
- [ ] Route tags on all untagged routes in `main.py` — prerequisite for APIREF-03
- [ ] `docs/requirements.txt` — add `mkdocs-swagger-ui-tag==0.8.0`
- [ ] No existing AppRoutes vitest tests — `npm run build` (TypeScript compilation) is sufficient to confirm Docs import removal

---

## Sources

### Primary (HIGH confidence)

- mkdocs-swagger-ui-tag official docs: https://blueswen.github.io/mkdocs-swagger-ui-tag/
- mkdocs-swagger-ui-tag options: https://blueswen.github.io/mkdocs-swagger-ui-tag/options/
- PyPI mkdocs-swagger-ui-tag 0.8.0 (released 2026-02-22): https://pypi.org/project/mkdocs-swagger-ui-tag/
- FastAPI discussions #7445 — openapi schema generation without server: https://github.com/fastapi/fastapi/discussions/7445
- Project files directly inspected: `puppeteer/agent_service/main.py`, `puppeteer/agent_service/db.py`, `puppeteer/agent_service/security.py` (import behavior), `puppeteer/dashboard/src/views/Docs.tsx`, `puppeteer/dashboard/src/layouts/MainLayout.tsx`, `puppeteer/dashboard/src/AppRoutes.tsx`, `docs/Dockerfile`, `docs/mkdocs.yml`, `docs/requirements.txt`, `puppeteer/cert-manager/Caddyfile`, `.planning/STATE.md`

### Secondary (MEDIUM confidence)

- doctave.com export guide — verified against FastAPI discussions and project source: https://www.doctave.com/blog/python-export-fastapi-openapi-spec
- Phase 20 summaries (20-01-SUMMARY.md, 20-02-SUMMARY.md) — confirmed Phase 20 state: build context, nginx config, compose service

### Tertiary (LOW confidence)

- FastAPI issue #1490 — side effect behavior at import: https://github.com/fastapi/fastapi/issues/1490 (issue closed as duplicate; behavior confirmed by reading db.py directly)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — mkdocs-swagger-ui-tag 0.8.0 confirmed on PyPI; app.openapi() pattern confirmed in FastAPI discussions; both verified against project source code
- Architecture: HIGH — all patterns derived directly from reading current codebase (Dockerfile, AppRoutes.tsx, MainLayout.tsx, main.py, db.py, security.py)
- Pitfalls: HIGH — ENCRYPTION_KEY risk verified by reading security.py directly; build context issue verified by reading compose.server.yaml; tag coverage verified by counting tags in main.py

**Research date:** 2026-03-16
**Valid until:** 2026-04-16 (mkdocs-swagger-ui-tag patch releases may occur; re-verify version if > 30 days)
