# Phase 24: Extended Feature Guides & Security - Research

**Researched:** 2026-03-17
**Domain:** Technical writing — MkDocs Material, operator documentation, security procedures
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Security guide reader level**
- Assumed knowledge: Novice operator — knows what TLS and Docker are, has run `docker compose` before, but has never touched PKI (no prior OpenSSL or cert knowledge assumed)
- Define all PKI terms on first use: CA, CRL, CSR, enrollment, etc.
- Include background boxes before complex procedures where needed
- Commands are fully explained — not just shown

**Security section structure**
- Opens with a Security Overview page (`security/index.md`) before the individual guides
- Overview content: 2–3 paragraphs explaining the defence-in-depth model (how mTLS + Ed25519 + RBAC + audit log form layered security), one Mermaid diagram showing the layers, then a table of contents to the individual guides
- Overview includes a Compromise Scenarios table: orchestrator compromised (Ed25519 still blocks unsigned scripts), node compromised (mTLS + container isolation limits blast radius), credential leaked (token_version invalidation)
- Overview frames each control in terms of the threat it mitigates

**Command formatting**
- Sensitive values (JOIN_TOKEN, private keys, cert paths, secrets) use `<PLACEHOLDER>` syntax in all code blocks
- Example: `JOIN_TOKEN=<YOUR_JOIN_TOKEN> docker compose up -d`
- Consistent across all Security and Feature Guide pages in this phase

**Security risk callouts**
- Use `!!! danger` admonition for hard limits and irreversible actions (consistent with Phase 23 pattern)
- Use `!!! warning` for operational risks (e.g., weak JWT secret, private key on disk)
- No separate "Security Warning" summary sections — inline admonitions at the point of risk

**mTLS guide**
- Full CA setup covered here — generating Root CA, creating JOIN_TOKEN, initial node enrollment. Setup & deployment guide (Phase 22) cross-links to this guide for the security-focused explanation
- Cert rotation: Full step-by-step with verification commands after every step — numbered steps, expected output shown, operator can't skip a verification step
- Point of no return (revoke old cert): Both a prerequisites checklist at the start of the rotation section AND a `!!! danger` admonition immediately before the revoke command
  - Checklist: "Before starting cert rotation, verify: [ ] new cert enrolled, [ ] node shows as Active in dashboard"
  - Danger box: "After this step, the old certificate is permanently revoked. Ensure the node has successfully enrolled with its new cert before proceeding."

**RBAC guide split (FEAT-04 vs SECU-02)**
- Task-split by audience purpose:
  - FEAT-04 (`feature-guides/rbac.md`) = "Using RBAC" — UI workflow: create users, assign roles, manage service principals through the dashboard. Operational guide.
  - SECU-02 (under Security section) = "RBAC Hardening" — which permissions to grant per role, least-privilege patterns, what to audit. Prescriptive security guidance.
- Service principals: Dedicated H2 section within FEAT-04 (not woven into user management) — machine identity vs human identity is a distinct concept. Cross-link from OAuth guide.
- Permission matrix: Standalone reference page `feature-guides/rbac-reference.md` with the full table of which permissions each role has by default. Both FEAT-04 and SECU-02 link to it. Neither guide is table-heavy.

**Job scheduling guide (FEAT-03)**
- Cron syntax: Brief intro (one paragraph explaining 5-field format + MoP-specific fields: second, timezone) + reference table of common patterns (every 5 min, daily at 2am, weekdays only, etc.). Link to an external cron visual generator for complex expressions. Not a cron tutorial.
- Node targeting: Covers both targeting modes side by side — capability targeting (OS family, runtime tags) and explicit node/group targeting. Comparison helps operators choose the right model.
- Staging review: Brief recap paragraph + cross-link to mop-push guide ("Scheduled jobs go through the same DRAFT→ACTIVE lifecycle. See the mop-push guide for the full Staging view walkthrough."). No full duplication.

**OAuth / authentication guide (FEAT-05)**
- Token lifecycle: Full coverage — expiry (how long, how to check), forced revocation (password change invalidates all sessions via `token_version`), service principal tokens vs user tokens, how to revoke a specific session
- Device flow: Conceptual explanation (what RFC 8628 device flow is, why MoP uses it — no redirect URI needed in CLI context) + cross-link to mop-push guide for step-by-step. OAuth guide owns the "why", mop-push guide owns the "how".
- CI/CD integration section: Practical section — create service principal, generate API key, set as CI secret, example `curl` / `mop-push` command. Covers the machine-auth pipeline use case. Fits here because it's about machine identity/auth.

**Air-gap guide (SECU-04)**
- Format: Narrative walkthrough (each area: package mirroring setup, offline build validation, outbound network restrictions) with a printable summary checklist at the end for audit mode
- Offline state verification: Includes a concrete test procedure — build with `--no-cache` while outbound network is blocked and confirm success
- Post-setup package additions: Dedicated section on the upload workflow (admin uploads .whl or .deb to the mirror sidecar after initial setup)
- Docs container offline: Brief section confirming MkDocs container is already offline-capable (privacy + offline plugins) and noting how to build the docs image without external deps
- "What still requires internet" section: Explicit list of what cannot be air-gapped — Cloudflare tunnel (must be replaced with on-prem alternative for full air-gap), initial base image pulls, any external Smelter lookups. Enterprise operators need to know exactly what to substitute.

### Claude's Discretion

- Section ordering within each guide beyond the structural decisions above
- Exact Mermaid diagram style for the Security overview
- Internal cross-linking strategy between feature guides
- Whether audit log guide uses a table of all event types or a structured list
- Tone and formatting conventions within the novice-level reading target

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FEAT-03 | Job scheduling guide covers JobDefinitions, cron syntax, capability targeting, and staging review | APScheduler cron fields confirmed from scheduler_service.py; DB model fields from ScheduledJob; staging statuses from status governance code |
| FEAT-04 | RBAC guide covers roles, permissions, user management, and service principals | Full role/permission seed data from main.py lifespan; ServicePrincipal model from db.py; _SPUserProxy pattern confirmed |
| FEAT-05 | OAuth/authentication guide covers device flow, token lifecycle, and API key usage | Device flow implementation confirmed in main.py; ACCESS_TOKEN_EXPIRE_MINUTES=1440; token_version invalidation logic confirmed; API key prefix format `mop_` confirmed |
| SECU-01 | mTLS guide covers Root CA setup, JOIN_TOKEN, cert enrollment, revocation, and rotation | pki.py fully read; node cert validity = 825 days; CA validity = 10 years; CRL next_update = 7 days; RevokedCert table confirmed |
| SECU-02 | RBAC configuration guide covers role assignment, permission grants, and least-privilege setup | Canonical permission sets confirmed from main.py seed; require_permission factory pattern confirmed; admin bypass behavior confirmed |
| SECU-03 | Audit log guide covers event types, query patterns, and compliance use cases | Full audit action inventory extracted from main.py grep; AuditLog schema confirmed (timestamp, username, action, resource_id, detail JSON) |
| SECU-04 | Air-gap operation guide covers package mirroring, offline builds, and network isolation | Privacy plugin + offline plugin confirmed in mkdocs.yml; MirrorConfigUpdate model confirmed; ApprovedIngredient mirror_status field confirmed |
</phase_requirements>

---

## Summary

Phase 24 is a pure documentation phase. There is no new backend or frontend code to write — all source-of-truth systems already exist and are running. The work is extracting accurate facts from the codebase, organising them for a novice operator audience, and writing eight new Markdown files across two doc sections.

The primary risk in this phase is inaccuracy: a guide that confidently documents the wrong cron field order, wrong permission name, or wrong cert validity period is worse than no guide at all. Every claim about system behaviour must trace to a specific source file. The secondary risk is scope creep — particularly for the mTLS and RBAC guides, where it is tempting to document aspirational features rather than what is implemented.

The tertiary risk is mkdocs.yml: `mkdocs build --strict` is enforced in the Docker builder stage, and any nav entry that references a file that does not yet exist will fail the build. New files must be added to the nav and created simultaneously, not one before the other.

**Primary recommendation:** Write stub files first (nav entry + title + one sentence), confirm `mkdocs build --strict` passes, then fill content plan-by-plan. Never add a nav entry without a corresponding file.

---

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| MkDocs Material | Already installed in docs container | Static site generator + theme | Established in Phase 20; all extensions already configured |
| pymdownx.superfences | Already enabled | Mermaid diagram rendering | Used in architecture.md; pattern established |
| admonition | Already enabled | `!!! danger` / `!!! warning` / `!!! tip` blocks | Pattern established in Phases 22–23 |
| pymdownx.details | Already enabled | Collapsible sections | Already in mkdocs.yml |
| tables extension | Already enabled | Markdown tables | Already in mkdocs.yml |

### No New Dependencies

This phase introduces no new MkDocs plugins, no new Python packages, and no new npm dependencies. The existing docs container build handles everything.

---

## Architecture Patterns

### Nav Structure to Add

The planner must update `docs/mkdocs.yml` with these additions (exact nav YAML):

```yaml
- Feature Guides:
    - Operator Tools:
        - mop-push CLI: feature-guides/mop-push.md
    - Platform Config:
        - Foundry: feature-guides/foundry.md
        - Job Scheduling: feature-guides/job-scheduling.md
        - RBAC: feature-guides/rbac.md
        - OAuth & Authentication: feature-guides/oauth.md
    - Reference:
        - RBAC Permission Reference: feature-guides/rbac-reference.md
- Security:
    - Overview: security/index.md
    - mTLS & Certificates: security/mtls.md
    - RBAC Hardening: security/rbac-hardening.md
    - Audit Log: security/audit-log.md
    - Air-Gap Operation: security/air-gap.md
```

### New Files Required

```
docs/docs/feature-guides/
├── job-scheduling.md    # FEAT-03
├── rbac.md              # FEAT-04
├── oauth.md             # FEAT-05
└── rbac-reference.md    # FEAT-04 reference page

docs/docs/security/
├── index.md             # Replace stub — SECU overview
├── mtls.md              # SECU-01
├── rbac-hardening.md    # SECU-02
├── audit-log.md         # SECU-03
└── air-gap.md           # SECU-04
```

Total: 9 files (1 replacement + 8 new).

### Established Writing Patterns (from Phases 22–23)

- H1 title = page name as operator would say it (e.g., "Job Scheduling" not "JobDefinition Management")
- First paragraph: one-sentence purpose, one-sentence prerequisite reference if needed
- `---` horizontal rules between major H2 sections
- Admonitions inline at the point of the gotcha, never collected into a "Pitfalls" section
- UI labels quoted exactly as they appear in the dashboard (e.g., **Nodes** not "the nodes page")
- No screenshots — reference UI labels only
- Code blocks use bash fencing with copy button (Material theme default)
- Tables: pipe syntax, always include header row
- Cross-links use relative paths: `../feature-guides/mop-push.md`

---

## Source of Truth for Each Guide

### FEAT-03: Job Scheduling (job-scheduling.md)

**Cron engine:** APScheduler `AsyncIOScheduler` with `'cron'` trigger.

**Cron field mapping** (confirmed from `scheduler_service.py` line 93):
```
schedule_cron split by whitespace → parts[0]=minute, parts[1]=hour, parts[2]=day, parts[3]=month, parts[4]=day_of_week
```
The `schedule_cron` field is a **5-field standard cron** (`minute hour day month day_of_week`). APScheduler supports standard cron syntax including `*`, `/`, `-`, and `,` operators.

**Status lifecycle** (confirmed from `scheduler_service.py`):
- `DRAFT` — created via mop-push, not yet promoted
- `ACTIVE` — running, will fire on schedule
- `DEPRECATED` — scheduler skips firing (logs `job:deprecated_skip`)
- `REVOKED` — scheduler skips firing (logs `job:revoked_skip`)
- Cron overlap guard: if a previous instance is still `PENDING`/`ASSIGNED`/`RETRYING`, the new fire is skipped and logged as `job:cron_skip`

**Targeting fields** (`ScheduledJob` model in `db.py`):
- `target_node_id` — specific node UUID
- `target_tags` — JSON list of tags, e.g. `["gpu", "secure"]`
- `capability_requirements` — JSON dict of required capabilities

**Retry fields** (`ScheduledJob` model):
- `max_retries` — int, default 0
- `backoff_multiplier` — float, default 2.0
- `timeout_minutes` — nullable int

**Signature requirement:** Every `ScheduledJob` must have `signature_id` and `signature_payload`. The scheduler validates the signature before creating the execution job (via `SignatureService`).

### FEAT-04: RBAC Guide (rbac.md + rbac-reference.md)

**Roles** (confirmed from `User` model, `main.py` `ALLOWED_ROLES`): `admin`, `operator`, `viewer`.

**Operator permissions** (from `main.py` lifespan seed, lines 174–180):
```
jobs:read, jobs:write, nodes:read, nodes:write,
definitions:read, definitions:write, foundry:read, foundry:write,
signatures:read, signatures:write, tokens:write,
alerts:read, alerts:write,
webhooks:read, webhooks:write
```

**Viewer permissions** (from `main.py` lifespan seed, lines 181–184):
```
jobs:read, nodes:read, definitions:read, foundry:read, signatures:read, alerts:read
```

**Admin:** Bypasses all permission checks entirely (no DB lookup needed). Admin is the only role that can manage users and permissions.

**Service Principals** (`ServicePrincipal` model in `db.py`):
- `client_id` — UUID, the identifier used in tokens
- `client_secret_hash` — bcrypt hash of the generated secret
- `role` — defaults to `"operator"`, can be any valid role
- `expires_at` — nullable; SP tokens rejected if past this date
- `is_active` — flag; SP tokens rejected if false
- Token type field: `"type": "service_principal"` in JWT payload

**_SPUserProxy** pattern (from `main.py`): Service principals masquerade as users for permission checks. `username` is set to `sp:<name>` for audit log attribution.

**Permission cache** (`_perm_cache` in `main.py`): Permissions are cached per role to avoid per-request DB queries. Cache is invalidated by `_invalidate_perm_cache(role)` when permissions change.

**User signing keys** (`UserSigningKey` model): Per-user Ed25519 keys stored in DB. The private key may be stored encrypted (`encrypted_private_key` nullable field).

**User API keys** (`UserApiKey` model):
- Prefix stored in `key_prefix` (first 12 chars) for lookup without full scan
- Authentication: token starts with `"mop_"` triggers `_authenticate_api_key()`
- Key hash compared via `verify_password()` (bcrypt)
- `permissions` field (nullable Text) — scoped subset of permissions

### FEAT-05: OAuth & Authentication (oauth.md)

**Device flow implementation** (RFC 8628, confirmed from `main.py`):
- `POST /auth/device` — initiates flow, returns `device_code`, `user_code`, `verification_uri`, `expires_in` (300s), `interval` (5s)
- `POST /auth/device/token` — polls with `device_code`, returns `slow_down` / `authorization_pending` / JWT
- `GET /auth/device/approve` — serves inline HTML approval page; operator enters credentials and approves
- `POST /auth/device/approve` — admin submits approval
- In-memory storage (`_device_codes` dict) — device codes are NOT persisted across restarts
- TTL: 300 seconds (5 minutes)
- One-time use: code is consumed after `POST /auth/device/token` succeeds

**Token lifecycle** (from `auth.py`):
- Algorithm: HS256
- Default expiry: `ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 = 1440` minutes (24 hours)
- JWT payload fields: `sub` (username), `role`, `tv` (token_version), `exp`
- Device flow tokens also include `"type": "device_flow"`
- Service principal tokens include `"type": "service_principal"`, `"sp_id"`

**Token invalidation** (from `main.py` `get_current_user()`):
- Any password change increments `User.token_version`
- All prior tokens rejected because `payload.get("tv", 0) != user.token_version`
- Effect is immediate — no TTL wait

**Password change routes:**
- `PATCH /auth/me` — self-service; requires `current_password` unless `must_change_password` is set; returns new token
- `POST /admin/users/{username}/reset-password` — admin reset; does NOT require current password; increments `token_version`

**Service principal tokens:**
- `POST /auth/service-principals/{id}/token` — returns short-lived JWT with `"type": "service_principal"`
- SP secret rotation: `POST /auth/service-principals/{id}/rotate` — new secret returned once, old secret immediately invalid

**API key auth flow:**
- Send `Authorization: Bearer mop_<key>` header
- `get_current_user()` detects `mop_` prefix → `_authenticate_api_key()`
- Scoped permissions from `UserApiKey.permissions` are not yet enforced (nullable, stored but not checked in current code — document as "future use" or validate in code review before writing)

### SECU-01: mTLS Guide (security/mtls.md)

**Root CA facts** (from `pki.py`):
- Key: RSA 4096-bit
- Algorithm: SHA-256
- Validity: 3650 days (10 years)
- CN: "Master of Puppets Root CA" / Org: "Bambibanners"
- CA directory: `secrets/ca/` (production); mounted at `/app/global_certs/` when cert-manager is in use
- Files: `root.key` (CA private key), `root.crt` (CA certificate)

**Node client cert facts** (from `pki.py` `sign_csr()`):
- Validity: **825 days** (~2.25 years)
- Algorithm: SHA-256
- CN: `<hostname>` (from CSR)
- BasicConstraints: `CA=False`

**Enrollment flow** (confirmed from codebase):
1. Node decodes `JOIN_TOKEN` to extract Root CA PEM
2. Node generates RSA private key + CSR
3. Node sends CSR to `POST /api/enroll`
4. Server signs CSR → returns PEM cert
5. Node stores cert in `secrets/` volume
6. Node uses cert for all subsequent `/work/pull` and `/heartbeat` calls

**CRL** (from `pki.py` `generate_crl()`):
- Next update: 7 days from generation
- Format: PEM-encoded X.509 CRL
- Endpoint: `GET /system/crl.pem` (unauthenticated)
- `RevokedCert` table: stores `serial_number`, `node_id`, `revoked_at`

**Revocation effect** (confirmed from `main.py`):
- Revoked nodes return 403 at `/work/pull` and `/api/enroll`
- `Node.status` set to `"OFFLINE"` on revoke

**PKI service fallback** (from `pki_service.py`):
- If `/app/global_certs/root_ca.crt` exists: uses cert-manager CA
- Otherwise: self-managed CA in `secrets/ca/`

**Cert rotation procedure** (must document — no automated tooling exists):
1. Generate new enrollment token
2. Stop and delete node container
3. Delete node cert volume (`secrets/` directory)
4. Restart node with JOIN_TOKEN — it will re-enroll and get new cert
5. Verify node appears as Active in dashboard
6. Revoke old cert (admin → Nodes → Revoke)
7. Verify CRL at `GET /system/crl.pem` contains old serial

**Warning:** There is no automated cert rotation command. The rotation procedure involves container lifecycle management (stop, delete volume, restart). This must be documented clearly for novice operators.

### SECU-02: RBAC Hardening (security/rbac-hardening.md)

This guide is prescriptive — "do this, not that" — rather than procedural. Key content areas:

**Least-privilege patterns:**
- Viewer role for monitoring-only operators (no write access to jobs/nodes)
- Operator role for day-to-day job management (no user management)
- Admin only for initial setup and user provisioning — do not use admin for day-to-day work
- Service principals for CI/CD — use operator role, not admin

**Audit-ability:**
- Admin actions are fully audited (user:create, user:delete, permission:grant, permission:revoke)
- SP actions are audited under `sp:<name>` username
- API key actions audited under owning user's username

**Permission grant/revoke API** (from `main.py`):
- `POST /admin/roles/{role}/permissions` — body: `{"permission": "jobs:read"}`
- `DELETE /admin/roles/{role}/permissions/{permission}`
- Both require `users:write` permission (admin-only in default config)

### SECU-03: Audit Log (security/audit-log.md)

**Complete audit action inventory** (extracted from `main.py` grep):

| Category | Actions |
|----------|---------|
| Authentication | `device_flow:token_issued`, `device_flow:approved`, `device_flow:denied` |
| User management | `user:create`, `user:delete`, `user:role_change`, `user:password_changed`, `user:password_reset`, `user:signing_key_created`, `user:signing_key_deleted`, `user:api_key_created`, `user:api_key_revoked` |
| Service principals | `sp:created`, `sp:updated`, `sp:deleted`, `sp:secret_rotated` |
| Permissions | `permission:grant`, `permission:revoke` |
| Jobs | `job:cancel`, `job:retry`, `job:pushed`, `job:cron_skip`, `job:draft_skip`, `job:revoked_skip`, `job:deprecated_skip` |
| Nodes | `node:delete`, `node:revoke`, `node:clear_tamper`, `node:upgrade_staged`, `node:reinstate` |
| Foundry | `template:build`, `template:delete`, `blueprint:delete`, `foundry:image_status_updated` |
| Signing keys | `key:upload`, `signature:delete` |
| Smelter/Mirror | `smelter:ingredient_added`, `smelter:ingredient_deactivated`, `smelter:config_updated`, `mirror:config_updated`, `smelter:package_uploaded`, `smelter:scan_triggered` |
| System | `base_image:marked_updated`, `signal:fire` |

**AuditLog schema** (from `db.py`):
```
id: int (auto)
timestamp: datetime
username: str (user or "sp:<name>" or "scheduler")
action: str
resource_id: str | None
detail: str | None (JSON-encoded dict)
```

**API endpoint:** `GET /admin/audit-log` — requires `users:write` (admin-only).

**Query patterns to document** (for compliance reporting):
- Filter by username to see all actions by a specific user
- Filter by action prefix (e.g., `node:`) to see node lifecycle events
- Filter by resource_id to trace all events on a specific node or job
- Time-range queries for compliance windows

### SECU-04: Air-Gap Operation (security/air-gap.md)

**What is already offline-capable** (HIGH confidence):
- MkDocs docs container: `privacy` plugin + `offline` plugin (already in mkdocs.yml) — zero runtime outbound requests
- Python package mirror: `ApprovedIngredient` model with `mirror_status`, `mirror_path`; `MirrorConfigUpdate` model with `pypi_mirror_url`, `apt_mirror_url`
- Foundry builds: use mirrored package index when configured
- Blueprint validation: Smelter can operate against mirrored registry

**What cannot be air-gapped** (must document honestly):
- Cloudflare Tunnel (used for dashboard public access): requires outbound to `*.cloudflare.com` — must be replaced with on-prem reverse proxy (Traefik, nginx, HAProxy) for full air-gap
- Initial base image pulls (`python:3.12-alpine`, `debian:12-slim`, etc.): must pre-pull to a local registry before disconnecting
- PowerShell installation in DEBIAN capability matrix recipe: downloads from `github.com/PowerShell/PowerShell/releases` — must mirror .deb/.tar.gz to local artifact store and update injection recipe
- Any `pip install` that does not use `pypi_mirror_url` config

**Mirror config update API** (from `main.py` `audit` call at line 2887):
- `PATCH /admin/mirror-config` with `{"pypi_mirror_url": "...", "apt_mirror_url": "..."}`
- Logs `mirror:config_updated`

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cron expression explanation | Custom cron tutorial section | One paragraph + reference table + link to crontab.guru | Cron is well-documented elsewhere; a full tutorial adds length without value |
| Permission table generation | Dynamic rendering | Static Markdown table in rbac-reference.md | The permission set is fixed; a static table is maintainable and searchable |
| Cert generation tooling | OpenSSL commands | Document the dashboard JOIN_TOKEN flow | The platform manages PKI; operators should use the platform, not OpenSSL |
| Audit log query UI | Custom query builder docs | SQL patterns against the DB + API filter params | The audit log is accessed via API and optionally direct DB |

---

## Common Pitfalls

### Pitfall 1: Nav / File Mismatch Fails Docker Build

**What goes wrong:** A nav entry in `mkdocs.yml` references a file that does not exist yet. `mkdocs build --strict` fails with a warning-as-error. The Docker builder stage fails.

**Why it happens:** Files are written before nav is updated, or nav is updated speculatively.

**How to avoid:** Add nav entry and create the file in the same plan. The established pattern from Phase 23 is stub-first: create the file with just a title and one sentence, then fill content.

**Warning signs:** Any `mkdocs build --strict` run that exits non-zero with "Documentation file" warnings.

### Pitfall 2: Documenting Aspirational Features

**What goes wrong:** The RBAC guide documents scoped API key permissions as if they are enforced, when the code stores `permissions` in `UserApiKey` but does not check them in `get_current_user()`.

**Why it happens:** DB model has the field; it looks like it should be enforced.

**How to avoid:** Verify every claimed behaviour against the actual auth path in `main.py`. The `_authenticate_api_key()` function does NOT check `UserApiKey.permissions` — it returns the full user object, which then passes full user role checks. Document as "the `permissions` field is reserved for future per-key permission scoping; currently the key grants the same access as the owning user's role."

**Warning signs:** Any statement "API keys can be scoped to specific permissions" — not yet true.

### Pitfall 3: Wrong Cron Field Order

**What goes wrong:** The guide documents the cron field order incorrectly (e.g., APScheduler uses named kwargs so the mapping matters). Standard cron is `minute hour day month day_of_week`. APScheduler's `add_job(..., 'cron', minute=..., hour=..., ...)` uses the same semantics.

**How to avoid:** The `schedule_cron` string is split and mapped as: `parts[0]→minute, parts[1]→hour, parts[2]→day, parts[3]→month, parts[4]→day_of_week`. This is confirmed from `scheduler_service.py` line 93. A 6-field cron string (with seconds) would fail to parse — do not document 6-field syntax.

### Pitfall 4: Cert Rotation Without Prerequisites Check

**What goes wrong:** Operator revokes the old cert before the node has successfully enrolled with the new cert. The node goes offline and cannot re-enroll because its cert is now revoked and the enrollment endpoint returns 403 for revoked nodes.

**Why it happens:** Rotation guide skips the verification step.

**How to avoid:** The prerequisites checklist and `!!! danger` admonition are locked decisions. Both must appear in the guide before the revoke command. Never allow the revoke step to be presented without the node-is-active verification step immediately before it.

### Pitfall 5: Security Overview Mermaid Syntax Error

**What goes wrong:** Mermaid diagram syntax error causes the docs build to emit a warning (rendered as JS error in browser, not a strict-mode failure, but looks bad).

**How to avoid:** Use the same Mermaid pattern as `developer/architecture.md` — test locally before committing. Prefer `graph TD` or `flowchart TD` over `sequenceDiagram` for the defence-in-depth model (simpler syntax, less error-prone).

---

## Code Examples

Verified from source files:

### Cron expression field mapping (scheduler_service.py:93)
```python
parts = j.schedule_cron.split()
# len(parts) must == 5
self.scheduler.add_job(
    self.execute_scheduled_job,
    'cron',
    args=[j.id],
    minute=parts[0],   # field 0
    hour=parts[1],     # field 1
    day=parts[2],      # field 2
    month=parts[3],    # field 3
    day_of_week=parts[4],  # field 4
    id=j.id,
    misfire_grace_time=60
)
```

### Token version invalidation (main.py:321)
```python
if payload.get("tv", 0) != user.token_version:
    raise credentials_exception
```

### Device flow TTL and interval constants (main.py:781-782)
```python
_DEVICE_TTL_SECONDS = 300   # 5 minutes
_POLL_INTERVAL_SECONDS = 5
```

### Role permission seed — complete set (main.py:174-188)
```python
OPERATOR_PERMS = [
    "jobs:read", "jobs:write", "nodes:read", "nodes:write",
    "definitions:read", "definitions:write", "foundry:read", "foundry:write",
    "signatures:read", "signatures:write", "tokens:write",
    "alerts:read", "alerts:write",
    "webhooks:read", "webhooks:write",
]
VIEWER_PERMS = [
    "jobs:read", "nodes:read", "definitions:read", "foundry:read", "signatures:read",
    "alerts:read",
]
```

### Node client cert validity (pki.py:136)
```python
.not_valid_after(
    datetime.datetime.now(UTC) + datetime.timedelta(days=825)
)
```

### API key prefix detection (main.py:292)
```python
if token.startswith("mop_"):
    return await _authenticate_api_key(token, db)
```

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|-----------------|-------|
| Security stub page | Full 5-page Security section | Phase 24 replaces `security/index.md` stub |
| No feature guides for scheduling/RBAC/auth | 4 new feature guide pages | Fills Platform Config nav section |
| mop-push guide owns device flow how-to | OAuth guide owns "why", mop-push owns "how" | Cross-link pattern established in CONTEXT.md |

---

## Open Questions

1. **API key scoped permissions**
   - What we know: `UserApiKey.permissions` field exists (nullable Text); `_authenticate_api_key()` returns the full owning `User` object without checking `permissions`
   - What's unclear: Was this intentional (future use) or an oversight?
   - Recommendation: Document as "currently the key grants the same access as the owning user's role; per-key scoping is planned". Do not document it as enforced.

2. **Device code in-memory storage**
   - What we know: `_device_codes` is an in-memory dict; not persisted
   - What's unclear: Whether this should be called out as a limitation in the OAuth guide
   - Recommendation: Yes, document with a `!!! warning` — "Device codes are stored in memory and are lost on server restart. If the server restarts during the 5-minute authorization window, the login flow must be restarted."

3. **Cert rotation for cert-manager CA path**
   - What we know: `pki_service.py` has two code paths — self-managed CA (`secrets/ca/`) and cert-manager CA (`/app/global_certs/`)
   - What's unclear: The mTLS guide should probably address which path is active in the default Docker Compose deployment
   - Recommendation: Default Docker Compose uses self-managed CA. The cert-manager path is only active when running with the Caddy cert-manager sidecar. Document the self-managed path as the primary procedure; note the cert-manager path exists for advanced deployments.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (backend), vitest (frontend) |
| Config file | `puppeteer/pytest.ini` (or default); `puppeteer/dashboard/vitest.config.ts` |
| Quick run command | `cd puppeteer && pytest tests/test_staging.py -x` (proxy for doc accuracy) |
| Full suite command | `cd puppeteer && pytest` |

### Phase Requirements → Test Map

This phase produces only documentation files (.md). None of the requirements (FEAT-03, FEAT-04, FEAT-05, SECU-01, SECU-02, SECU-03, SECU-04) require new automated tests — the underlying features are already tested in existing test files. The documentation accuracy cannot be verified by automated tests.

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FEAT-03 | Scheduler cron field mapping matches documentation | manual verification | Review `scheduler_service.py:93` against guide | N/A — code review |
| FEAT-04 | Permission seed matches rbac-reference.md table | manual verification | Review `main.py:174-188` against guide | N/A — code review |
| FEAT-05 | Device flow TTL/interval values in guide match code | manual verification | Review `main.py:781-782` against guide | N/A — code review |
| SECU-01 | Cert validity values in guide match pki.py | manual verification | Review `pki.py:136` against guide | N/A — code review |
| SECU-01–04 | mkdocs build --strict passes after all files added | automated build check | `docker compose -f puppeteer/compose.server.yaml build docs` | ✅ existing |
| All | Nav entries all resolve to existing files | build check | `mkdocs build --strict` in builder stage | ✅ existing |

### Sampling Rate

- **Per task commit:** Non-strict local mkdocs build: `cd docs && mkdocs build 2>&1 | grep -i warning` (catches broken links)
- **Per wave merge:** Full Docker build of docs container to confirm `--strict` passes
- **Phase gate:** All 9 files exist, nav is updated, Docker build passes before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `docs/docs/feature-guides/job-scheduling.md` — stub required before nav entry added (FEAT-03)
- [ ] `docs/docs/feature-guides/rbac.md` — stub required (FEAT-04)
- [ ] `docs/docs/feature-guides/oauth.md` — stub required (FEAT-05)
- [ ] `docs/docs/feature-guides/rbac-reference.md` — stub required (FEAT-04 reference)
- [ ] `docs/docs/security/mtls.md` — stub required (SECU-01)
- [ ] `docs/docs/security/rbac-hardening.md` — stub required (SECU-02)
- [ ] `docs/docs/security/audit-log.md` — stub required (SECU-03)
- [ ] `docs/docs/security/air-gap.md` — stub required (SECU-04)

`security/index.md` already exists (replacing stub content, no new file needed for nav).

---

## Sources

### Primary (HIGH confidence)

- `puppeteer/agent_service/main.py` — complete permission seed, audit action inventory, device flow implementation, token_version invalidation, API key auth
- `puppeteer/agent_service/pki.py` — cert validity periods, CRL generation, CA parameters
- `puppeteer/agent_service/db.py` — all model schemas: ScheduledJob, AuditLog, ServicePrincipal, UserApiKey, RevokedCert, Node
- `puppeteer/agent_service/auth.py` — JWT algorithm, expiry duration (1440 min), token structure
- `puppeteer/agent_service/services/scheduler_service.py` — cron field mapping, status skip logic, overlap guard
- `puppeteer/agent_service/services/pki_service.py` — CA path fallback logic
- `docs/mkdocs.yml` — current nav structure, enabled extensions
- `docs/docs/security/index.md` — current stub content (to be replaced)
- `docs/docs/feature-guides/foundry.md` — writing pattern reference
- `docs/docs/feature-guides/mop-push.md` — writing pattern reference, device flow how-to pattern

### Secondary (MEDIUM confidence)

- APScheduler cron trigger field semantics: standard cron order confirmed from library docs pattern (`minute hour day month day_of_week`)
- RFC 8628 device flow: implementation confirmed against standard error codes (`authorization_pending`, `slow_down`, `access_denied`, `expired_token`)

### Tertiary (LOW confidence)

None — all claims traceable to project source files.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all tools verified from mkdocs.yml
- Architecture (file layout, nav): HIGH — confirmed from existing docs structure and mkdocs.yml
- Source facts (cron fields, cert validity, permissions, audit actions): HIGH — directly read from source files
- Writing patterns: HIGH — confirmed from Phases 22–23 docs files
- Pitfalls: HIGH — most derived from known strict-mode constraint (Phase 23 established) and code inspection

**Research date:** 2026-03-17
**Valid until:** Stable — based on source code review, not external APIs. Valid until any of the referenced source files change.
