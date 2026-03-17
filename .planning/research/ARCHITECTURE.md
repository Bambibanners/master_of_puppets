# Architecture Research

**Domain:** Pull-architecture job orchestrator — v10.0 feature integration (output capture, runtime attestation, retry policy, environment tags, CI/CD dispatch)
**Researched:** 2026-03-17
**Confidence:** HIGH — based on direct codebase analysis (db.py, job_service.py, main.py, node.py, models.py)

---

## Existing Architecture Baseline

### System Overview

```
                         ORCHESTRATOR (puppeteer/)
  ┌──────────────────────────────────────────────────────────────┐
  │  React Dashboard (Vite)          Caddy (TLS termination)     │
  │  puppeteer/dashboard/src/views/  ← /docs/* → nginx (MkDocs) │
  ├──────────────────────────────────────────────────────────────┤
  │  FastAPI (agent_service/main.py)                             │
  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐    │
  │  │ job_service │  │ scheduler_   │  │ foundry_service  │    │
  │  │    .py      │  │ service.py   │  │ alert_service    │    │
  │  └──────┬──────┘  └──────────────┘  └──────────────────┘    │
  │         │  SQLAlchemy ORM (create_all, no Alembic)           │
  │  ┌──────▼──────────────────────────────────────────────┐     │
  │  │  PostgreSQL (prod) / SQLite (dev)                   │     │
  │  │  jobs, nodes, execution_records, scheduled_jobs...  │     │
  │  └─────────────────────────────────────────────────────┘     │
  └──────────────────────────────────────────────────────────────┘
               ▲ mTLS (client cert)     ▲ mTLS (client cert)
               │                        │
  ┌────────────┴──────┐        ┌────────┴────────────┐
  │  Puppet Node A    │        │  Puppet Node B       │
  │  node.py          │        │  node.py             │
  │  polls /work/pull │        │  polls /work/pull    │
  │  reports to       │        │  reports to          │
  │  /work/{guid}/    │        │  /work/{guid}/result │
  │  result           │        └─────────────────────┘
  └───────────────────┘
```

### Current Data Flow: Job Execution

```
1. Operator dispatches job (POST /jobs) or APScheduler fires (scheduler_service.py)
2. Job inserted into `jobs` table with status=PENDING
3. Node polls POST /work/pull → job_service.pull_work()
   - Filters PENDING/RETRYING jobs by tag matching, env: isolation, capability matching, memory limit
   - Assigns job: status=ASSIGNED, node_id set, started_at set
   - Returns WorkResponse (guid, task_type, payload, limits)
4. Node executes: runtime.py → Docker/Podman/direct subprocess
5. Node reports: POST /work/{guid}/result with ResultReport
   - job_service.report_result() writes ExecutionRecord + updates Job.status
   - Retry logic: RETRYING state with retry_after backoff if retriable=True
   - Dependency unblocking: _unblock_dependents() on COMPLETED
   - Webhook dispatch on terminal status
```

### What Already Exists (Critical — do not re-implement)

| Feature | Where It Lives | State |
|---------|----------------|-------|
| `ExecutionRecord` table | `db.py` lines 216-233 | Complete — job_guid, node_id, status, exit_code, started_at, completed_at, output_log (JSON), truncated |
| `output_log` written by node | `node.py` `build_output_log()` + `report_result()` | Complete — JSON list of {t, stream, line} entries |
| Output written to `execution_records` | `job_service.report_result()` lines 708-719 | Complete — with 1 MB truncation and secret scrubbing |
| `GET /api/executions` + `GET /api/executions/{id}` | `main.py` lines 430-515 | Complete — pagination, node_id/status/job_guid filter |
| `GET /jobs/{guid}/executions` | `main.py` lines 1461-1486 | Complete — per-job execution history |
| Retry policy on `Job` | `db.py` Job columns: max_retries, retry_count, retry_after, backoff_multiplier | Complete — exponential backoff with jitter in `job_service.py` |
| `RETRYING` / `DEAD_LETTER` job states | `job_service.report_result()` lines 736-766 | Complete |
| Zombie reaper (timeout-triggered retry) | `job_service.pull_work()` lines 221-273 | Complete |
| `env:` tag isolation in node selection | `job_service.pull_work()` lines 312-322 | Complete — env: prefix treated as strict isolation |
| `retriable` flag on `ResultReport` | `models.py` line 63 | Complete — node opts in via `retriable=True` |
| `WorkResponse.max_retries / backoff_multiplier / timeout_minutes` | `models.py` line 52-54 | Complete — passed to node but node.py doesn't use them yet |

### What Is Missing for v10.0

| Requirement | Gap Description |
|-------------|-----------------|
| OUTPUT-01/02 | Node captures output — DONE. Server stores it — DONE. But `WorkResponse` doesn't tell node the retry config (backoff/max_retries) and node.py doesn't set `retriable=True` on failure yet |
| OUTPUT-03/04 | Dashboard UI for execution history — missing in frontend views |
| OUTPUT-05/06/07 | Runtime attestation — entirely absent. No signing in node.py, no verification in job_service.py, no attestation fields on ExecutionRecord |
| RETRY-01 | `ScheduledJob` has `max_retries`/`backoff_multiplier` columns but scheduler_service.py doesn't propagate them to created `Job` records |
| RETRY-03 | Dashboard UI showing attempt N of M — missing |
| ENVTAG-01 | `Node.tags` exists but no dedicated `env_tag` column — currently env tags are stored as `env:DEV` strings in the generic tags JSON list; no first-class field |
| ENVTAG-02 | Job dispatch accepts `target_tags` with env: prefix — the enforcement is already there, but no explicit `env_tag` field in the dispatch API |
| ENVTAG-03 | Dashboard Nodes view doesn't surface env tag visually or as a filter |
| ENVTAG-04 | CI/CD dispatch endpoint — absent. No structured `POST /api/dispatch` with JSON response format |
| All | `ExecutionRecordResponse` missing attestation fields (attestation_bundle, attestation_verified) |

---

## Feature Integration Architecture

### Feature 1: Job Output Capture (OUTPUT-01 through OUTPUT-04)

**Status: ~80% complete in backend. Frontend work is the main gap.**

The node already calls `build_output_log()` and passes `output_log` + `exit_code` to `report_result()`. The server writes an `ExecutionRecord`. The `/api/executions` endpoint exists.

**Two backend gaps to close:**

1. **Node.py does not set `retriable=True`** — the node never signals the orchestrator that a failure was a clean (retriable) exit vs a crash. This gates retry policy.

2. **WorkResponse doesn't echo retry config to node** — `max_retries` and `backoff_multiplier` are in `WorkResponse` (models.py) but `job_service.pull_work()` doesn't populate them from `Job` columns. Node.py ignores them anyway.

   Recommendation: populate them in `pull_work()`. Node.py can use them for local timeout enforcement (already has `timeout_minutes` handling). The retry decision stays server-side; node only needs to signal `retriable=True` for non-zero exits.

**Modified components:**
- `node.py` `execute_task()` — set `retriable=True` when exit_code != 0 and it is not a security rejection
- `job_service.pull_work()` — populate `max_retries`, `backoff_multiplier`, `timeout_minutes` in `WorkResponse`
- Frontend `Jobs.tsx` — add execution history drawer/tab showing output_log entries

**New API endpoints needed:** None — `/api/executions` and `/jobs/{guid}/executions` already exist.

**DB changes:** None — `ExecutionRecord` table is complete.

---

### Feature 2: Runtime Attestation (OUTPUT-05, OUTPUT-06, OUTPUT-07)

**Status: Absent. New code required throughout the pipeline.**

**Concept:** After executing a job, the node constructs a deterministic bundle, signs it with its mTLS private key, and includes the signature in `ResultReport`. The orchestrator verifies the signature against the stored `client_cert_pem` on the `Node` record.

**Attestation bundle structure (canonical, deterministic):**

```
bundle = {
    "script_hash": sha256(script_content),
    "stdout_hash": sha256(stdout),
    "stderr_hash": sha256(stderr),
    "exit_code": int,
    "start_ts": ISO8601 UTC string,
    "node_cert_serial": str (from node's own cert)
}
serialised = json.dumps(bundle, sort_keys=True, separators=(',', ':'))
```

Node signs `serialised.encode('utf-8')` using its RSA-2048 private key (at `secrets/{NODE_ID}.key`) with PKCS1v15 + SHA256, producing a base64-encoded signature.

**Key constraint — RSA, not Ed25519:** The node's mTLS key is RSA-2048 (generated in `node.py ensure_identity()` at line 380). Attestation signing uses this same key. The orchestrator already stores the node's full `client_cert_pem` which contains the public key — no new key material needs to be transmitted.

**Node-side changes (node.py):**

```python
# In execute_task(), after result is obtained:
attestation_bundle = build_attestation_bundle(
    script=script,
    stdout=result.get("stdout", ""),
    stderr=result.get("stderr", ""),
    exit_code=result["exit_code"],
    start_ts=job_started_at,         # pass via job dict (WorkResponse must include started_at)
    key_file=self.key_file,
    cert_file=self.cert_file,
)
await self.report_result(guid, ..., attestation=attestation_bundle)
```

New helper `build_attestation_bundle()` in node.py:
- Builds canonical JSON bundle
- Signs with `cryptography.hazmat.primitives.asymmetric.padding.PKCS1v15` + SHA256
- Returns `{"bundle": <serialised_json>, "signature": <base64>, "cert_serial": <serial>}`

**Orchestrator-side changes (job_service.py):**

```python
# In report_result(), after writing ExecutionRecord:
if report.attestation:
    verification_result = verify_attestation(
        attestation=report.attestation,
        node_cert_pem=node.client_cert_pem
    )
    record.attestation_bundle = report.attestation.get("bundle")
    record.attestation_signature = report.attestation.get("signature")
    record.attestation_verified = verification_result   # "VERIFIED" / "FAILED" / "MISSING"
```

New helper `verify_attestation()` in `services/attestation_service.py`:
- Load public key from `node.client_cert_pem` via `x509.load_pem_x509_certificate().public_key()`
- Verify RSA PKCS1v15 signature
- Returns verification status string

**DB changes — ExecutionRecord table needs 3 new columns:**

```python
# In db.py ExecutionRecord:
attestation_bundle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)     # raw JSON bundle
attestation_signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # base64 signature
attestation_verified: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # VERIFIED/FAILED/MISSING
```

**Migration SQL for existing deployments:**

```sql
ALTER TABLE execution_records ADD COLUMN IF NOT EXISTS attestation_bundle TEXT;
ALTER TABLE execution_records ADD COLUMN IF NOT EXISTS attestation_signature TEXT;
ALTER TABLE execution_records ADD COLUMN IF NOT EXISTS attestation_verified VARCHAR(20);
```

**Models changes:**
- `ResultReport` — add `attestation: Optional[Dict] = None`
- `ExecutionRecordResponse` — add `attestation_verified: Optional[str] = None`, `attestation_bundle: Optional[str] = None`

**New API endpoint for export (OUTPUT-07):**

```
GET /api/executions/{id}/attestation
→ Returns: {bundle, signature, cert_serial, verified}
Auth: history:read permission
```

**WorkResponse must include `started_at`** — the node needs the server-assigned start timestamp for the bundle to be reproducible. Add `started_at: Optional[datetime] = None` to `WorkResponse` and populate it in `pull_work()` when `started_at` is set.

---

### Feature 3: Retry Policy (RETRY-01, RETRY-02, RETRY-03)

**Status: Orchestrator logic complete. Two gaps: scheduler propagation and node.py signaling.**

**Gap 1: Scheduler does not propagate retry config to dispatched jobs**

`ScheduledJob` has `max_retries` and `backoff_multiplier` columns (db.py lines 79-80). When APScheduler fires and creates a `Job`, `scheduler_service.py` must copy these values into the `Job` row.

```python
# In scheduler_service.py, when creating a Job from a ScheduledJob:
new_job = Job(
    ...
    max_retries=sched_job.max_retries,
    backoff_multiplier=sched_job.backoff_multiplier,
    timeout_minutes=sched_job.timeout_minutes,
)
```

Ad-hoc dispatch (`POST /jobs`) already accepts `max_retries` via `JobCreate` — check that `JobCreate` model exposes these fields and `create_job()` passes them to the `Job` constructor.

**Gap 2: Node must signal `retriable=True` for non-security failures**

`report_result()` in job_service.py only retries when `report.retriable is True`. The node currently never sets this. The node should set `retriable=True` whenever the failure is a clean non-zero exit (not a signature verification failure or memory limit rejection).

```python
# node.py report_result() signature — node decides retriable:
retriable = (not security_rejected) and (exit_code is not None) and (exit_code != 0)
```

**Gap 3: Dashboard display (RETRY-03)**

`ExecutionRecord` already stores all attempts (one record per attempt). The `Job` row has `retry_count` and `max_retries`. The dashboard can show "Attempt {retry_count + 1} of {max_retries + 1}" by reading the job detail alongside execution history.

No backend changes needed — this is frontend work in `Jobs.tsx`.

---

### Feature 4: Environment Tags (ENVTAG-01 through ENVTAG-04)

**Status: The enforcement logic is already complete. Missing: first-class column, UI, and CI/CD endpoint.**

**Current implementation:** `env:` tags are stored in `Node.tags` (or `Node.operator_tags`) as strings like `"env:PROD"`. Job matching in `pull_work()` already enforces strict env: isolation (lines 312-322). This works correctly and is the right design.

**Gap 1: No dedicated `env_tag` column on Node (ENVTAG-01)**

The existing tags approach works, but ENVTAG-01 calls for a configurable environment tag. The cleanest path is to add a first-class `env_tag` column to `Node` so it:
- Is visible separately from capability/feature tags in API responses
- Can be set at enrollment time (via `JOIN_TOKEN` payload extension or env var on node)
- Appears clearly in dashboard filtering

```python
# db.py Node addition:
env_tag: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # DEV, TEST, PROD, or custom
```

**Migration SQL:**

```sql
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS env_tag VARCHAR(64);
```

At enrollment, the node can pass `env_tag` in the heartbeat payload. The server stores it on `Node.env_tag`. The existing `env:` tag isolation logic in `pull_work()` continues to use the tags list — the new `env_tag` column feeds the new CI/CD dispatch endpoint and dashboard display.

**Alternative:** Keep the `env:` tags approach (already enforced correctly), populate `Node.env_tag` by extracting the `env:` prefix tag from `operator_tags` at read time (no schema change). This avoids a migration for fresh deployments and is simpler. Recommended for v10.0.

**Node declaration (ENVTAG-01):** Add `ENV_TAG` env var to node compose files. `heartbeat_loop()` reads it and includes it in the heartbeat payload. `receive_heartbeat()` writes it to `operator_tags` as `env:<ENV_TAG>` if not already set by operator.

**Gap 2: CI/CD dispatch endpoint (ENVTAG-04)**

New endpoint:

```
POST /api/dispatch
Auth: Bearer token or API key (operator permission: jobs:write)
Body: {
    "job_definition_id": str,       # ScheduledJob.id
    "env_tag": str,                 # "DEV" | "TEST" | "PROD" | custom
    "override_tags": [str],         # optional additional tag constraints
    "timeout_minutes": int          # optional override
}
Response: {
    "job_guid": str,
    "status": "PENDING",
    "node_assigned": null,          # filled once assigned at next poll
    "env_tag": str,
    "job_definition": str           # name
}
```

Implementation: looks up the `ScheduledJob`, validates its `status == "ACTIVE"`, constructs a `Job` with `target_tags` including `env:<env_tag>`, and returns the structured JSON. The endpoint must be documented as the CI/CD integration path.

**Gap 3: NodeResponse must expose env_tag (ENVTAG-03)**

`NodeResponse` in models.py needs `env_tag: Optional[str] = None`. The `list_nodes()` handler in main.py must extract env_tag from `operator_tags` (or the new column) and include it in the response dict.

---

### Feature 5: CI/CD Dispatch API (ENVTAG-04 — detailed)

**Auth approach:** Service principals already exist (`ServicePrincipal` table, `_SPUserProxy`). CI/CD pipelines should authenticate using a service principal's `client_id` + `client_secret` via `POST /auth/service-principal/token` to get a short-lived JWT, then use that JWT as Bearer for `POST /api/dispatch`.

Alternatively, a service principal API key (`mop_` prefix) can authenticate directly — this is already wired in `security.py`. This is simpler for CI/CD (one credential, no token exchange). Recommended.

**Response contract:** The response must be stable (not change between minor versions) and include enough for a pipeline to poll job status:

```json
{
    "job_guid": "abc-123",
    "status": "PENDING",
    "job_definition": "deploy-frontend",
    "env_tag": "PROD",
    "poll_url": "/jobs/abc-123/executions"
}
```

The CI/CD caller can poll `GET /jobs/{guid}` or `GET /jobs/{guid}/executions` for completion.

---

## Recommended Component Boundaries

### New Files to Create

| File | Purpose |
|------|---------|
| `puppeteer/agent_service/services/attestation_service.py` | `verify_attestation()` — loads public key from PEM, verifies RSA PKCS1v15 + SHA256 signature |
| (no new DB file) | ExecutionRecord columns added directly to `db.py` |

### Files to Modify

| File | Changes |
|------|---------|
| `puppeteer/agent_service/db.py` | Add 3 attestation columns to `ExecutionRecord`; optionally add `env_tag` to `Node` |
| `puppeteer/agent_service/models.py` | Extend `ResultReport` (attestation field); extend `ExecutionRecordResponse` (attestation fields); add `DispatchRequest`/`DispatchResponse` models; add `env_tag` to `NodeResponse` |
| `puppeteer/agent_service/services/job_service.py` | `pull_work()`: populate retry config in WorkResponse; `report_result()`: call `verify_attestation()`, write attestation columns |
| `puppeteer/agent_service/services/scheduler_service.py` | Propagate `max_retries`, `backoff_multiplier`, `timeout_minutes` to created `Job` |
| `puppeteer/agent_service/main.py` | Add `POST /api/dispatch` endpoint; add `GET /api/executions/{id}/attestation` endpoint; update `list_nodes()` to expose `env_tag` |
| `puppets/environment_service/node.py` | Add `build_attestation_bundle()` helper; set `retriable=True` for non-security failures; pass `ENV_TAG` in heartbeat; include `attestation` in `report_result()` call |
| `puppeteer/dashboard/src/views/Jobs.tsx` | Execution history panel with output_log display, retry state (attempt N of M) |
| `puppeteer/dashboard/src/views/Nodes.tsx` | Show `env_tag` badge, add env_tag filter |
| Migration SQL file (e.g. `migration_v14.sql`) | ALTER TABLE for new columns on `execution_records` (and optionally `nodes`) |

---

## Data Flow: Attestation

```
Node executes job:
  script → runtime.py → {stdout, stderr, exit_code}
  │
  ├─ build_attestation_bundle()
  │    bundle = {script_hash, stdout_hash, stderr_hash, exit_code, start_ts, cert_serial}
  │    serialised = json.dumps(bundle, sort_keys=True, separators=(',',':'))
  │    sig = RSA_key.sign(serialised.encode(), PKCS1v15(), SHA256())
  │    return {bundle: serialised, signature: base64(sig), cert_serial: ...}
  │
  └─ POST /work/{guid}/result
       ResultReport.attestation = {bundle, signature, cert_serial}
       ResultReport.retriable = (exit_code != 0 and not security_rejected)
       ResultReport.output_log = build_output_log(stdout, stderr)

Orchestrator receives result:
  job_service.report_result()
  │
  ├─ Write ExecutionRecord (output_log, exit_code, status) — existing
  │
  ├─ IF attestation present:
  │    cert_pem = node.client_cert_pem
  │    public_key = x509.load_pem_x509_certificate(cert_pem).public_key()
  │    public_key.verify(b64decode(sig), serialised.encode(), PKCS1v15(), SHA256())
  │    record.attestation_verified = "VERIFIED" or "FAILED"
  │    record.attestation_bundle = bundle_json
  │    record.attestation_signature = sig_b64
  │
  └─ Continue with retry / dependency logic — existing
```

---

## Data Flow: Environment Tag + CI/CD Dispatch

```
Node startup:
  ENV_TAG=PROD env var → heartbeat payload includes env_tag
  Orchestrator.receive_heartbeat() → stores "env:PROD" in operator_tags (if not already set by operator)

CI/CD pipeline:
  POST /api/dispatch  (service principal API key)
    body: {job_definition_id, env_tag: "PROD"}
  │
  ├─ Lookup ScheduledJob → validate ACTIVE status
  ├─ Build Job with target_tags = existing_tags + ["env:PROD"]
  ├─ Copy max_retries, backoff_multiplier, timeout_minutes from ScheduledJob
  ├─ INSERT jobs → status=PENDING
  └─ Return {job_guid, status, job_definition, env_tag, poll_url}

Next node poll cycle:
  Node with operator_tags=["env:PROD"] polls /work/pull
  pull_work() matches env: tag constraint → assigns job
  Node executes → reports result with attestation
```

---

## Recommended Build Order

Dependencies constrain this order:

**Phase A: Backend completeness (closes all backend gaps — enables testing without UI)**

1. **Output capture wiring** (1-2 days)
   - `node.py`: set `retriable=True` for non-security failures
   - `job_service.pull_work()`: populate `max_retries`, `backoff_multiplier`, `timeout_minutes` in `WorkResponse`
   - `scheduler_service.py`: propagate retry config from `ScheduledJob` to `Job`
   - No schema changes needed

2. **Environment tags first-class** (0.5 days)
   - Add `ENV_TAG` env var support to `heartbeat_loop()` in `node.py`
   - Update `receive_heartbeat()` to store it as `env:<value>` in operator_tags (if not already set)
   - Add `env_tag` (derived from tags, no schema change) to `NodeResponse`
   - Update `NodeConfig` to echo env_tag back to node

3. **Attestation: node side** (1-2 days)
   - Add `build_attestation_bundle()` helper to `node.py`
   - Requires `cryptography` lib (already a dependency — used for CSR generation)
   - Include `attestation` dict in `report_result()` call
   - Requires `WorkResponse.started_at` so the bundle uses the server-assigned timestamp

4. **Attestation: orchestrator side** (1-2 days)
   - `db.py`: add 3 columns to `ExecutionRecord`
   - `migration_v14.sql` for existing deployments
   - `attestation_service.py`: `verify_attestation()` using `cryptography` RSA verify
   - `job_service.report_result()`: call verify_attestation, write columns
   - `models.py`: extend `ResultReport`, `ExecutionRecordResponse`
   - `GET /api/executions/{id}/attestation` endpoint

5. **CI/CD dispatch endpoint** (1 day)
   - `models.py`: `DispatchRequest`, `DispatchResponse`
   - `main.py`: `POST /api/dispatch`
   - Auth via existing service principal API key flow

**Phase B: Frontend (closes UI gaps — can be done in parallel with Phase A after step 1)**

6. **Execution history UI** (`Jobs.tsx`) — output_log display, retry state
7. **Nodes env_tag display** (`Nodes.tsx`) — badge, filter
8. **Attestation status in execution detail** — show VERIFIED/FAILED/MISSING badge

---

## Architecture Constraints to Preserve

| Constraint | Why It Matters | How v10.0 Respects It |
|------------|----------------|----------------------|
| Pull-only model | Nodes work across NAT, no inbound ports needed | Attestation is included in the existing `report_result()` call — no new connections |
| Nodes are stateless between polls | No state survives container restarts except `secrets/` volume | Attestation uses the persisted mTLS key from `secrets/{node_id}.key` |
| mTLS for all node communication | Node identity is cryptographically bound | Attestation reuses the mTLS client cert public key — no new key material |
| No migration framework | `create_all` won't ALTER existing tables | Migration SQL file for all new columns |
| SQLite + Postgres compatibility | Dev and prod must both work | All new columns use types supported by both (TEXT, VARCHAR, INTEGER) |
| Secrets never in logs | `report_result()` already scrubs secrets from output_log | Attestation bundle hashes stdout/stderr (hashes don't leak secrets) |
| env: tags controlled by operator, not node | Prevents node self-escalation (SEC-02 in job_service.py) | `ENV_TAG` env var sets operator_tags on first heartbeat; operator can override via `PATCH /nodes/{id}` |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Storing raw stdout/stderr in the attestation bundle

**What people do:** Include raw output in the bundle so verifiers can check it.
**Why it's wrong:** Output can contain secrets; bundle would bypass the existing scrubbing pipeline.
**Do this instead:** Hash stdout and stderr (SHA-256). The hash is in the bundle; the raw text is scrubbed then stored separately in `execution_records.output_log`.

### Anti-Pattern 2: Node generates a new signing key for attestation

**What people do:** Create a separate Ed25519 key for attestation to avoid reusing the mTLS key.
**Why it's wrong:** Introduces key management complexity; the new key has no binding to node identity; weakens the security model.
**Do this instead:** Sign with the RSA mTLS private key. The orchestrator already has the corresponding public key in `client_cert_pem`. The binding is established by the CA-signed enrollment.

### Anti-Pattern 3: CI/CD endpoint creates a new job type

**What people do:** Invent a new job dispatch mechanism with different fields and auth.
**Why it's wrong:** Creates a parallel dispatch path that bypasses existing validation (signature check, tag enforcement, memory limit checks).
**Do this instead:** `POST /api/dispatch` is a thin wrapper over the existing `Job` creation flow — it validates the `ScheduledJob`, builds a `Job` with the correct tags, and delegates to `create_job()`.

### Anti-Pattern 4: Retrying security-rejected jobs

**What people do:** Set `retriable=True` on all failures for simplicity.
**Why it's wrong:** Security-rejected jobs (signature failure, missing verification key) should not retry — the underlying issue is a policy violation, not a transient error. Retrying wastes capacity and obscures the security event.
**Do this instead:** `retriable = (exit_code is not None) and (not security_rejected)` — already the correct signal.

### Anti-Pattern 5: Adding env_tag as a separate targeting mechanism

**What people do:** Build a new targeting field and new matching logic parallel to the existing tags system.
**Why it's wrong:** The `env:` tag isolation in `pull_work()` already works correctly. Duplicating it creates two paths to reason about.
**Do this instead:** Use `env:<value>` convention in existing tags. The dedicated `env_tag` field on `Node` and `DispatchRequest` is only for ergonomics — internally it translates to the existing `env:` tag list entry.

---

## Integration Points

### Node ↔ Orchestrator Interface

| Endpoint | Direction | v10.0 Change |
|----------|-----------|--------------|
| `POST /work/pull` | Node → Orchestrator | `WorkResponse` must include `max_retries`, `backoff_multiplier`, `timeout_minutes`, `started_at` |
| `POST /work/{guid}/result` | Node → Orchestrator | `ResultReport` adds `attestation: Optional[Dict]`; node sets `retriable=True` for non-security failures |
| `POST /heartbeat` | Node → Orchestrator | `HeartbeatPayload` adds `env_tag: Optional[str]`; stored as `env:` operator tag |

### New Endpoints

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `POST /api/dispatch` | Bearer / API key (jobs:write) | CI/CD structured dispatch with env_tag |
| `GET /api/executions/{id}/attestation` | Bearer (history:read) | Export attestation bundle for offline verification |

### Existing Endpoints — No Change Required

| Endpoint | Reason |
|----------|--------|
| `GET /api/executions` | Already supports node_id, status, job_guid filters |
| `GET /jobs/{guid}/executions` | Already returns all execution records for a job |
| `POST /jobs` | Already accepts max_retries, target_tags for ad-hoc dispatch |
| `PATCH /nodes/{id}` | Already accepts tags for operator_tags override |

---

## Scalability Considerations

| Concern | At current scale (homelab/enterprise) | If scale grows |
|---------|---------------------------------------|----------------|
| ExecutionRecord growth | Index on job_guid and started_at already in place (db.py lines 229-233). 1 MB cap per log. | Add time-based pruning (keep last 90 days) — a Config key can control this |
| Attestation verification on every result | RSA verify is fast (~1ms). No concern at this scale. | If volume is extreme, verify async via background task |
| CI/CD dispatch throughput | Single dispatch per pipeline run. No concern. | Rate limiting via existing `slowapi` limiter |
| env_tag matching in pull_work | O(n) scan over PENDING/RETRYING jobs, capped at 50 candidates. Already acceptable. | Add DB index on `jobs.status` + `jobs.target_tags` if queue depth grows |

---

## Sources

- Direct codebase analysis: `db.py`, `models.py`, `main.py`, `job_service.py`, `node.py` (2026-03-17)
- `cryptography` library RSA signing: existing usage in `node.py ensure_identity()` (RSA-2048 key generation + CSR signing) confirms the library is available and the key format is consistent
- Requirements: `.planning/REQUIREMENTS.md` — OUTPUT-01..07, RETRY-01..03, ENVTAG-01..04
- Project context: `.planning/PROJECT.md` — v10.0 goals and architectural constraints

---

*Architecture research for: Axiom v10.0 — pull-architecture job orchestrator feature integration*
*Researched: 2026-03-17*
