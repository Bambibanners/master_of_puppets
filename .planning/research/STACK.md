# Stack Research

**Domain:** Enterprise job orchestration — Axiom v10.0 Commercial Release new features
**Researched:** 2026-03-17
**Confidence:** HIGH (codebase reviewed directly; PyPI Trusted Publisher prerequisites verified against official docs)

---

## Scope

This file covers ONLY the net-new stack additions for v10.0. The existing validated stack
(FastAPI, SQLAlchemy, React/Vite, APScheduler, cryptography, PyNaCl, Caddy, Postgres, aiosqlite,
MkDocs Material container) is not repeated here.

The previous STACK.md (v9.0) covered the MkDocs Material docs container; that content remains
valid and is not superseded.

---

## Pre-Assessment: What Already Exists

Before recommending additions, the codebase was audited directly. Several v10.0 requirements
are already partially or fully implemented:

| Requirement | Current State |
|-------------|---------------|
| OUTPUT-01/02: stdout/stderr/exit code per execution | `ExecutionRecord` table exists in `db.py` with `output_log` (JSON), `exit_code`, `truncated`. Node captures and reports these in `node.py` via `build_output_log()`. Job service writes records in `report_result()`. **Fully implemented.** |
| OUTPUT-03/04: Execution history query | `ExecutionRecord` has 4 composite indexes (`ix_execution_records_job_guid`, `job_started`, `node_started`, `started_at`). Query infrastructure is ready. Frontend view is the only missing piece. |
| RETRY-01/02/03: Retry policy with backoff | `Job` has `max_retries`, `retry_count`, `retry_after`, `backoff_multiplier`. `job_service.py` implements exponential backoff with jitter on failure and zombie reaping. `ScheduledJob` also has `max_retries`. **Fully implemented in the data model and job service.** |
| ENVTAG-01/02: Environment tags | `Node.operator_tags` accepts `env:DEV`, `env:TEST`, `env:PROD` tags. `job_service.pull_work()` has strict env-tag isolation logic (lines 312-322). `HeartbeatPayload` sanitises self-reported `env:` tags. **Fully implemented.** |

**Conclusion:** The core backend logic for OUTPUT, RETRY, and ENVTAG is already in the codebase.
v10.0 work is primarily:
1. Runtime attestation (OUTPUT-05..07) — new signing/verification step, new DB column
2. CI/CD dispatch API (ENVTAG-04) — a documented endpoint, likely already possible via existing `/jobs` POST + env tag
3. PyPI Trusted Publisher activation (RELEASE-01) — external org/project creation, no code changes
4. GHCR image publishing (RELEASE-02) — workflow already written, awaits org creation
5. Frontend views for execution history and retry state (OUTPUT-03/04, RETRY-03) — dashboard work only

---

## Recommended Stack

### New Backend: Runtime Attestation (OUTPUT-05..07)

No new Python libraries are required. The `cryptography` library already in
`puppeteer/requirements.txt` provides everything needed.

| Capability | How Achieved | Library |
|------------|-------------|---------|
| Sign attestation bundle on node | `cryptography.hazmat.primitives.asymmetric.padding.PKCS1v15` or `cryptography.hazmat.primitives.asymmetric.ec.ECDSA` via the node's RSA private key (already on disk at `secrets/{node_id}.key`) | `cryptography` (already present) |
| Verify attestation on orchestrator | Load stored `Node.client_cert_pem`, extract public key, verify signature bytes | `cryptography` (already present) |
| Serialise attestation bundle | `json.dumps` of bundle dict → `hashlib.sha256` → sign the canonical UTF-8 bytes | stdlib `json`, `hashlib` |

**Node private key format:** Nodes enroll with RSA 2048 keys (confirmed in `node.py` line 380:
`rsa.generate_private_key(public_exponent=65537, key_size=2048)`). The key is written to
`secrets/{node_id}.key` in PEM format without encryption. The attestation signer in `node.py`
should use `RSA + PKCS1v15 + SHA256` — the same algorithm family already used for CSR signing.

**DB addition needed:** `ExecutionRecord` needs two new nullable columns:

```python
attestation_bundle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # raw JSON bundle
attestation_signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # base64 signature
attestation_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # VERIFIED / FAILED / MISSING
```

These are nullable so existing records are not broken. `create_all` will not add them to the
existing table — a migration SQL file is required (same pattern as `migration_v13.sql`).

### New Backend: CI/CD Dispatch API (ENVTAG-04)

No new library required. The existing `POST /jobs` endpoint already accepts `target_tags`
(which can include `env:PROD`). What ENVTAG-04 requires is:

1. A documented, stable endpoint path for CI/CD consumers — recommend `/api/v1/dispatch` as
   a thin wrapper around the existing job creation flow, returning structured JSON.
2. Service Principal auth (already exists) is the correct auth mechanism for pipelines.
3. The response shape needs to include `node_assigned` (available after polling) or be
   asynchronous with a `job_id` for polling.

**Recommendation:** Add `GET /api/v1/jobs/{guid}/status` as a lightweight polling endpoint
that returns `{guid, status, node_id, exit_code, attempt}` — suitable for `curl` + `jq` in CI.
No new library needed.

### New Frontend: Execution History View (OUTPUT-03/04, RETRY-03)

No new npm packages required. All data is already queryable. The work is:

1. Add `GET /jobs/{guid}/executions` API route (returns list of `ExecutionRecord` rows for
   a job) — backend work, no new library.
2. Add an execution history panel to the Jobs view in `Jobs.tsx` or a dedicated
   `ExecutionHistory.tsx` — uses existing recharts (already in `package.json`) for timeline
   visualisation, existing Radix UI for the expanded log viewer.

**One potential addition:** A syntax-highlighted log viewer for stdout/stderr output.
`react-syntax-highlighter` (v15.x) is the standard choice, but the output format is plain text
line-by-line (not code), so a plain `<pre>` with line coloring by `stream` field is sufficient
and avoids a new dependency.

### PyPI Trusted Publisher (RELEASE-01)

No code changes required. The `release.yml` workflow is already correctly configured:
- Uses `pypa/gh-action-pypi-publish@release/v1`
- Has `permissions: id-token: write` on both publish jobs
- Targets `environment: testpypi` and `environment: pypi` with the correct URLs

**External prerequisites only:**

| Step | Action | Who |
|------|--------|-----|
| 1 | Create `axiom-laboratories` GitHub organisation | Operator |
| 2 | Transfer or fork this repo into `axiom-laboratories/axiom` | Operator |
| 3 | On PyPI: go to "Publishing" → "Add a new pending publisher" | Operator |
| 4 | Fill in: PyPI project name `axiom-sdk`, GitHub owner `axiom-laboratories`, repo `axiom`, workflow `release.yml`, environment `pypi` | Operator |
| 5 | Repeat step 3-4 for TestPyPI with environment `testpypi` | Operator |
| 6 | Push a `v*` tag — the workflow runs, PyPI creates the project and publishes | Operator |

**Critical:** The pending publisher does not reserve the name `axiom-sdk` on PyPI until the
first publish. If another account registers `axiom-sdk` before the first publish, the pending
publisher is invalidated. Publish as soon as the org and pending publisher are configured.

### GHCR Multi-Arch Publishing (RELEASE-02)

No code changes required. The `docker-release` job in `release.yml` is fully configured:
- Multi-arch: `linux/amd64,linux/arm64` via QEMU + buildx
- Pushes to `ghcr.io/axiom-laboratories/axiom`
- Tags: semver `{{version}}` and `{{major}}.{{minor}}`

**External prerequisite only:** The `axiom-laboratories` GitHub org must exist and the repo
must be under it. Once the org exists and the repo is transferred, pushing any `v*` tag
activates both PyPI and GHCR publishing simultaneously.

### Licence Compliance (LICENCE-01..04)

No new libraries required. This is documentation and configuration work:

| Task | File | Action |
|------|------|--------|
| LICENCE-01: certifi MPL-2.0 decision | `LEGAL.md` | Document read-only CA bundle usage, no source modification, obligations satisfied |
| LICENCE-02: License-Expression field | `pyproject.toml` | Add `license-expression = "Apache-2.0"` under `[project]` (PEP 639 field, supported by setuptools >=61) |
| LICENCE-03: NOTICE file | `NOTICE` | List caniuse-lite CC-BY-4.0 attribution and any others from audit |
| LICENCE-04: paramiko LGPL-2.1 assessment | `LEGAL.md` | Confirm dynamic-only import pattern; document whether EE bundling requires asyncssh swap |

**Note on `asyncssh`:** If LICENCE-04 assessment concludes that EE wheel bundling would
statically link paramiko, replace it with `asyncssh` (MIT). `asyncssh` is drop-in compatible
for SSH-over-Python use cases and avoids the LGPL-2.1 linking concern entirely. Do not swap
unless the assessment concludes static linking is occurring — dynamic import of paramiko is
fully LGPL-compliant without source distribution.

---

## Schema Additions Summary

All are additive (nullable columns or new index) — safe to add via migration SQL.

```sql
-- migration_v14.sql
-- Runtime attestation columns on execution_records

ALTER TABLE execution_records ADD COLUMN IF NOT EXISTS
    attestation_bundle TEXT;
ALTER TABLE execution_records ADD COLUMN IF NOT EXISTS
    attestation_signature TEXT;
ALTER TABLE execution_records ADD COLUMN IF NOT EXISTS
    attestation_status VARCHAR(20);

-- Environment tag on nodes (for ENVTAG-01 explicit column, if desired)
-- Note: env tags already work via operator_tags JSON column.
-- An explicit column is optional but aids filtering performance.
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS
    env_tag VARCHAR(20);
```

The `env_tag` column on `Node` is optional — the existing `operator_tags` JSON column already
supports `env:DEV` / `env:TEST` / `env:PROD` tags with enforced isolation in `pull_work()`.
Adding a dedicated column is recommended for ENVTAG-03 (filterable Nodes view) to avoid
parsing JSON in the DB query. If added, backfill from `operator_tags` at migration time.

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `cryptography` RSA+PKCS1v15 for attestation | `PyNaCl` Ed25519 for attestation | PyNaCl is already used for job signing. Using a different key type for attestation (node's mTLS RSA key) means we cannot reuse PyNaCl — the node's identity key is RSA, not Ed25519. Keeping `cryptography` for attestation uses the already-loaded key material. |
| stdlib `json` + `hashlib` for bundle serialisation | `msgpack` or CBOR for binary attestation | Binary formats add a new dependency for no operational benefit. JSON is inspectable, debuggable, and sufficient for offline verification by operators. |
| Existing `/jobs` POST for CI/CD dispatch | New dedicated `/api/v1/dispatch` endpoint | The existing endpoint already does everything needed. A thin wrapper adds a stable documented path without duplicating logic. Either approach works; the recommendation is to document the existing endpoint as the CI/CD interface and add the status-polling endpoint. |
| `asyncssh` (conditional swap for paramiko) | Keep `paramiko` in all cases | Paramiko is LGPL-2.1. Dynamic import is fine for open-source distribution. The swap is only needed if EE wheel bundling creates static linking — assess before deciding. |
| Dedicated `env_tag` column on nodes | Keep using `operator_tags` JSON | JSON parsing in SQL WHERE clauses is non-portable (differs between SQLite and Postgres). A dedicated column with an index makes the filter in ENVTAG-03 straightforward and consistent across both DB backends. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| New retry library (tenacity, backoff) | Retry logic with exponential backoff + jitter is already implemented in `job_service.py`. Adding a library would duplicate it. | Extend the existing `max_retries` / `backoff_multiplier` / `retry_after` pattern already in the `Job` model |
| New attestation library (sigstore, in-toto) | Heavyweight dependencies designed for software supply chain provenance, not runtime execution attestation. The requirement is a signed JSON bundle using the node's existing RSA key — that is 20 lines of `cryptography` code. | `cryptography` (already present) |
| `PyJWT` or `python-jose` for attestation tokens | JWTs are stateless bearer tokens, not signed execution records. The verification requirement needs the raw signature + stored cert. | Raw PKCS1v15 signature over the JSON bundle bytes |
| `aiosqlite` version pin changes | The existing `DATABASE_URL` sqlite+aiosqlite pattern is already working. No version changes needed for v10.0 features. | Keep existing aiosqlite as installed by sqlalchemy[asyncio] |
| New frontend charting library | recharts is already installed and used for sparklines. Execution timeline can use the same library. | recharts (already present) |

---

## Stack Patterns by Variant

**Attestation verification on orchestrator (OUTPUT-06):**
- Load `Node.client_cert_pem` from DB
- Parse with `cryptography.x509.load_pem_x509_certificate()`
- Extract public key: `cert.public_key()`
- Verify: `public_key.verify(signature_bytes, bundle_bytes, padding.PKCS1v15(), hashes.SHA256())`
- Catch `cryptography.exceptions.InvalidSignature` → store `attestation_status = "FAILED"`
- Success → store `attestation_status = "VERIFIED"`

**Attestation signing on node (OUTPUT-05):**
- Build bundle dict: `{script_hash, stdout_hash, stderr_hash, exit_code, started_at, node_cert_serial}`
- Canonical form: `json.dumps(bundle, sort_keys=True).encode("utf-8")`
- Load key: `serialization.load_pem_private_key(key_bytes, password=None)`
- Sign: `private_key.sign(bundle_bytes, padding.PKCS1v15(), hashes.SHA256())`
- Encode for transport: `base64.b64encode(signature).decode()`
- Include `attestation_bundle` (JSON string) and `attestation_signature` (base64 string) in the `ResultReport` POST body

**CI/CD dispatch pattern (ENVTAG-04):**
```bash
# Minimal CI/CD dispatch — no new tooling required
JOB_ID=$(curl -sf -X POST https://axiom.example.com/jobs \
  -H "Authorization: Bearer $SERVICE_PRINCIPAL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_type":"python_script","payload":{...},"target_tags":["env:PROD"]}' \
  | jq -r .guid)

# Poll for completion
while true; do
  STATUS=$(curl -sf https://axiom.example.com/api/v1/jobs/$JOB_ID/status \
    -H "Authorization: Bearer $SERVICE_PRINCIPAL_TOKEN" | jq -r .status)
  [ "$STATUS" = "COMPLETED" ] && break
  [ "$STATUS" = "FAILED" ] && exit 1
  sleep 5
done
```

---

## Version Compatibility

| Package | Version in requirements.txt | Notes for v10.0 |
|---------|---------------------------|-----------------|
| cryptography | unpinned (latest) | RSA PKCS1v15 signing available since cryptography 1.x. No version concern. Current latest is 44.x. |
| sqlalchemy | unpinned | `mapped_column` declarative syntax requires SQLAlchemy 2.0+. Already using it. New nullable columns are additive. |
| aiosqlite | transitive via sqlalchemy | SQLite `ADD COLUMN IF NOT EXISTS` requires SQLite 3.35+ (shipped in Python 3.10+). Project already requires Python 3.10+. |
| pyproject.toml setuptools | >=61.0 (already pinned) | `License-Expression` (PEP 639) requires setuptools >=62.3 for full support. Bump to `>=62.3` in `[build-system]`. |

---

## Installation

No new packages needed in `puppeteer/requirements.txt`.

For `pyproject.toml` build-system:
```toml
[build-system]
requires = ["setuptools>=62.3"]   # was >=61.0; bump for PEP 639 License-Expression
build-backend = "setuptools.build_meta"

[project]
# Add this field (PEP 639):
license-expression = "Apache-2.0"
# Remove the old:
# license = {text = "Apache-2.0"}
```

---

## Sources

- `puppeteer/agent_service/db.py` — reviewed directly; `ExecutionRecord`, `Job`, `Node` schemas confirmed (HIGH confidence)
- `puppeteer/agent_service/services/job_service.py` — retry logic, env-tag isolation, execution record writes confirmed (HIGH confidence)
- `puppets/environment_service/node.py` — RSA key generation (line 380), `build_output_log()`, `report_result()` confirmed (HIGH confidence)
- `puppeteer/agent_service/models.py` — `ResultReport` fields, `WorkResponse` fields confirmed (HIGH confidence)
- `puppeteer/requirements.txt` — existing dependencies confirmed; no new additions needed (HIGH confidence)
- `.github/workflows/release.yml` — PyPI OIDC publish jobs, GHCR multi-arch build confirmed (HIGH confidence)
- `pyproject.toml` — current `license = {text = "Apache-2.0"}` form confirmed; PEP 639 migration path identified (HIGH confidence)
- [PyPI Trusted Publishers — Creating a project through OIDC](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) — pending publisher prerequisites, name-squatting warning confirmed (HIGH confidence)
- [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish) — `id-token: write` requirement, `repository-url` for TestPyPI confirmed (HIGH confidence)
- [cryptography X.509 reference](https://cryptography.io/en/latest/x509/reference/) — `load_pem_x509_certificate`, `public_key()`, RSA verify API confirmed (HIGH confidence)
- [Python packaging — License-Expression (PEP 639)](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license) — setuptools >=62.3 requirement for PEP 639 field (MEDIUM confidence — cross-referenced with setuptools changelog)

---

*Stack research for: Axiom v10.0 — Commercial Release new features*
*Researched: 2026-03-17*
