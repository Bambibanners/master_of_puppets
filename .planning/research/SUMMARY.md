# Project Research Summary

**Project:** Axiom v10.0 — Commercial Release
**Domain:** Pull-architecture enterprise job orchestration platform
**Researched:** 2026-03-17
**Confidence:** HIGH

## Executive Summary

Axiom v10.0 is a commercial release milestone for a mature, deployed job orchestration platform that already has mTLS node enrollment, Ed25519 job signing, container-isolated execution, RBAC, service principals, cron scheduling, and a full dashboard. The core research finding is that the required v10.0 feature set is substantially more complete than a fresh implementation — the backend logic for output capture, retry policy, and environment tag enforcement already exists in `job_service.py`, `db.py`, and `node.py`. The development work consists of closing precise, well-understood gaps rather than building features from scratch. No new libraries are required. The release workflow is already correctly configured; only external org and project creation is blocking.

The recommended approach is a backend-first, frontend-second sequence. Three backend gaps gate all observable features: node.py must set `retriable=True` for non-security failures, scheduler_service must propagate retry config to dispatched jobs, and the attestation pipeline must be built end-to-end (node signs with its RSA mTLS key, orchestrator verifies against the stored `client_cert_pem`). These are self-contained, testable changes. The frontend execution history UI, retry state display, and env tag badges can be built in parallel once the APIs are stable. Licence compliance and release infrastructure (org creation, PyPI Trusted Publisher, GHCR activation) are fully independent of all code work and can proceed at any time before the first publish.

The highest-risk area is runtime attestation. The platform already uses Ed25519 for job script signing, which creates a strong temptation to copy that signing pattern for attestation — but the node's mTLS identity key is RSA-2048, not Ed25519. Using the wrong signing API or wrong argument count silently produces no valid attestation. The second highest risk is output retention: the `ExecutionRecord` table has no TTL and at cron-job scale will fill the database without a scheduled pruning task. Both risks have clear mitigations and must be addressed in the first phase that touches each feature.

## Key Findings

### Recommended Stack

No new libraries are required for v10.0. The `cryptography` library already present handles RSA PKCS1v15 attestation signing and cert public key extraction. `recharts` and Radix UI cover all frontend needs. The only build-system change is bumping `setuptools>=62.3` in `pyproject.toml` for PEP 639 `License-Expression` support (was `>=61.0`).

**Core technologies:**
- `cryptography` (existing): RSA-2048 attestation signing on node via `padding.PKCS1v15()` + `hashes.SHA256()`; cert public key extraction and RSA verify on orchestrator — no version pin needed, current latest is 44.x
- `sqlalchemy` (existing): three new nullable columns on `ExecutionRecord`, one optional column on `Node` — additive, safe via migration SQL
- `recharts` (existing): execution history timeline and retry state display in the dashboard — no new charting library
- `pypa/gh-action-pypi-publish` (existing in release.yml): OIDC Trusted Publisher flow already correctly wired; only org and project creation is blocking

**Schema additions (all additive, nullable):** `attestation_bundle TEXT`, `attestation_signature TEXT`, `attestation_verified VARCHAR(20)` on `execution_records`; optional `env_tag VARCHAR(64)` on `nodes`. All handled via `migration_v14.sql`.

See `.planning/research/STACK.md` for full migration SQL, signing pattern code samples, and version compatibility table.

### Expected Features

**Must have (P1 — v10.0 blocking):**
- Job output capture: stdout/stderr/exit code per execution stored in `ExecutionRecord` — backend ~80% complete, node.py gap to close
- Execution history queries: per job definition and per node, paginated — API already exists, dashboard UI missing
- Retry policy: max retries + fixed/exponential backoff with jitter — orchestrator logic complete, scheduler propagation gap to close
- Runtime attestation: node signs execution bundle with mTLS RSA key; orchestrator verifies against stored cert — entirely absent, new code required throughout the pipeline
- Environment tags: `ENV_TAG` on nodes with strict isolation in job dispatch — enforcement logic already present, first-class column and structured UI missing
- CI/CD dispatch API: structured `POST /api/dispatch` with polling response — absent, new endpoint required
- Licence compliance: LEGAL.md, NOTICE, `license-expression` in pyproject.toml, paramiko LGPL-2.1 assessment — documentation work, no code changes
- Release infrastructure: axiom-laboratories org + PyPI Trusted Publisher + GHCR activation — external prerequisites only

**Should have (P2):**
- Non-retryable exit code list per job definition
- Attestation export endpoint `GET /api/executions/{id}/attestation`
- Nodes view env tag badge and filter
- Public docs access decision (remove CF Access or document rationale)

**Defer (v11.0+):**
- Live log streaming via WebSocket — breaks pull model by design; post-execution capture covers 95% of operator needs
- Environment-scoped RBAC — requires permission model extension
- SLSA provenance format — custom attestation bundle covers the functional need
- Log shipping integrations (Elasticsearch, Loki)
- Signed releases via sigstore/cosign

See `.planning/research/FEATURES.md` for full prioritization matrix, feature dependency graph, and competitor analysis table.

### Architecture Approach

The v10.0 feature integration follows a "thin wiring" pattern: the orchestrator already has the data model, query infrastructure, and enforcement logic for most features. The work is connecting existing pieces (scheduler propagates retry config to created jobs), adding new signing steps to an existing data flow (attestation in `report_result()`), and exposing first-class API surfaces for patterns that already work implicitly (env tags via `operator_tags`). One genuinely new component is `attestation_service.py` — a small focused module for RSA verify that isolates the cryptographic logic from `job_service.py`.

**Major components touched in v10.0:**
1. `node.py` — add `build_attestation_bundle()` helper; set `retriable=True` for non-security failures; pass `ENV_TAG` in heartbeat payload
2. `job_service.py` — populate retry config in `WorkResponse`; call `verify_attestation()` in `report_result()`; write attestation columns
3. `scheduler_service.py` — propagate `max_retries`, `backoff_multiplier`, `timeout_minutes` from `ScheduledJob` to created `Job` rows
4. `main.py` — add `POST /api/dispatch` and `GET /api/executions/{id}/attestation` endpoints; expose `env_tag` in `list_nodes()`
5. `attestation_service.py` (new file) — `verify_attestation()` using RSA PKCS1v15 verify against stored node cert
6. `Jobs.tsx` — execution history panel with output_log rendered as terminal view, retry state badge showing attempt N of M
7. `Nodes.tsx` — env_tag badge column and filter control

**Architecture constraints that must be preserved:** Pull-only model (attestation stays in the existing `report_result()` POST); nodes stateless between polls (attestation uses persisted mTLS key from `secrets/` volume); env tags operator-controlled not node-reported (heartbeat sanitization strips self-reported `env:` prefix tags).

See `.planning/research/ARCHITECTURE.md` for full data flow diagrams, attestation pipeline sequence, CI/CD dispatch flow, and anti-patterns to avoid.

### Critical Pitfalls

1. **RSA vs Ed25519 attestation signing** — The node's mTLS key is RSA-2048; existing job signing uses Ed25519. RSA requires `key.sign(data, padding.PKCS1v15(), hashes.SHA256())` — three args. RSA verify on the orchestrator also requires four args. Copying from `signature_service.py` produces wrong code that may fail silently. Prevention: write a unit test with RSA sign/verify round-trip against a test cert fixture before implementing node-side code.

2. **Output retention not added before history UI** — `ExecutionRecord` has no TTL. At 10 jobs/minute the table reaches gigabytes within days (1 MB cap per row). Add a scheduled APScheduler pruning task (30-day default) in the output capture phase. Note: SQLite requires `DELETE WHERE rowid IN (SELECT rowid ...)` pattern for subquery deletes — not `DELETE WHERE id IN (SELECT ... LIMIT N)`.

3. **Attestation bundle with incomplete fields** — Omitting `exit_code` or `cert_serial` from the signed JSON bundle means those fields can be tampered post-signing without invalidating the signature. Use `json.dumps(bundle, sort_keys=True, separators=(',',':'))` — `sort_keys=True` is mandatory for deterministic serialization across Python versions.

4. **Retry thundering herd on first attempt** — When a batch of jobs fails simultaneously, all retries share the same `retry_after` window. The existing ±20% jitter is insufficient for large batches (50 jobs × ±6s = 12-second pile-up window). Add a random initial offset of `random.uniform(0, 30)` seconds before the exponential component on first retry.

5. **`create_all` does not add new columns to existing tables** — Every new ORM column is silently ignored on existing deployments. Create `migration_v14.sql` at the start of v10.0 work and add to it incrementally as each feature phase adds columns.

6. **Attestation hashes computed post-scrub** — Computing stdout/stderr SHA-256 after secret scrubbing means independent verifiers cannot reproduce the hash (they have the raw output, not the redacted version). Order must be: `hash raw bytes → scrub → truncate → store`.

See `.planning/research/PITFALLS.md` for all 10 pitfalls with recovery strategies, integration gotchas table, and a "looks done but isn't" test checklist.

## Implications for Roadmap

The natural phase structure follows the dependency graph in FEATURES.md: schema and node-side changes must precede orchestrator verification; orchestrator APIs must precede dashboard UI; licence compliance and release infrastructure are fully independent.

### Phase 1: Backend Completeness — Output Capture + Retry Wiring

**Rationale:** Closes the three backend gaps that gate all observable features with no schema changes required (except initiating `migration_v14.sql`). Everything in this phase is testable via API before any UI exists. Output retention pruning must be included here — not deferred — because the table will grow without bound under test load.
**Delivers:** node.py sets `retriable=True`; scheduler propagates retry config to created jobs; `WorkResponse` includes `max_retries`/`backoff_multiplier`/`timeout_minutes`/`started_at`; APScheduler retention task for `execution_records` (30-day default, SQLite-compatible delete pattern)
**Addresses:** OUTPUT-01/02 (node gap closure), RETRY-01 (scheduler propagation), RETRY-02 (node signal)
**Avoids:** Output table unbounded growth (Pitfall 2), retry policy silently not applied to scheduled jobs

### Phase 2: Runtime Attestation — Node + Orchestrator

**Rationale:** Attestation is Axiom's primary commercial differentiator with no equivalent in Rundeck, Temporal, or any cloud scheduler. It requires changes to both the node agent and the orchestrator, and it is the most complex new feature. Building it as a self-contained phase allows full end-to-end testing before UI work begins. The attestation columns on `ExecutionRecord` are added to `migration_v14.sql` here.
**Delivers:** `build_attestation_bundle()` in node.py; `attestation_service.py` with RSA PKCS1v15 verify; `report_result()` calls verify and writes attestation columns; `ResultReport` model extended with `attestation: Optional[Dict]`; `GET /api/executions/{id}/attestation` endpoint
**Addresses:** OUTPUT-05, OUTPUT-06, OUTPUT-07
**Avoids:** RSA vs Ed25519 key confusion (Pitfall 1), incomplete bundle fields (Pitfall 3), post-scrub hash computation (Pitfall 6)
**Research flag:** The RSA signing pattern is novel in this codebase. The "looks done but isn't" checklist from PITFALLS.md (attestation round-trip unit test, bundle mutation test, secrets volume isolation test) must pass before this phase closes.

### Phase 3: Environment Tags + CI/CD Dispatch

**Rationale:** Env tag enforcement already works via the `env:` prefix in `operator_tags`. This phase promotes it to a first-class feature with a dedicated column, `ENV_TAG` env var support on nodes, and the structured dispatch endpoint. Depends on Phase 1 so retry config is available to propagate through the dispatch path.
**Delivers:** `env_tag` column on `Node` (migration SQL); `ENV_TAG` heartbeat support in node.py; `NodeResponse.env_tag`; `POST /api/dispatch` with service principal auth returning `{job_guid, status, job_definition, env_tag, poll_url}`; `DispatchRequest`/`DispatchResponse` models
**Addresses:** ENVTAG-01, ENVTAG-02, ENVTAG-04
**Avoids:** Env tag self-escalation via heartbeat (Pitfall 4), CI/CD dispatch returning PENDING indefinitely with no polling guidance (Pitfall 8)
**Research flag:** The 409 response when no eligible node exists at dispatch time is a product decision with UX implications. Confirm the response contract before documenting it as the stable CI/CD integration surface.

### Phase 4: Dashboard UI — Execution History, Retry State, Env Tags

**Rationale:** All backend APIs are stable after Phases 1-3. Frontend work can implement execution history, retry state display, and env badge without further API changes. This phase can be partially parallelised with Phase 3 — the Jobs.tsx execution history work has no dependency on env_tag.
**Delivers:** Execution history panel in Jobs.tsx (output_log rendered as terminal-style view with stdout/stderr colour coding; retry state badge showing attempt N/M); attestation VERIFIED/FAILED/MISSING badge in execution detail with link to runbook on failure; env_tag badge and filter in Nodes.tsx
**Addresses:** OUTPUT-03, OUTPUT-04, RETRY-03, ENVTAG-03
**Avoids:** Rendering raw JSON output_log to operators (UX pitfall), attestation failure with no operator guidance (UX pitfall)

### Phase 5: Licence Compliance + Release Infrastructure

**Rationale:** Fully independent of all feature code. Must complete before any `v*` tag is pushed. Doing this last minimises the PyPI name-squatting risk window — configure the pending publisher and publish immediately.
**Delivers:** `LEGAL.md` with certifi MPL-2.0 assessment and paramiko LGPL-2.1 assessment; `NOTICE` file with caniuse-lite CC-BY-4.0 attribution; `license-expression = "Apache-2.0"` and `setuptools>=62.3` in pyproject.toml; `axiom-laboratories` GitHub org; PyPI Trusted Publisher (pending publisher, not standard); GHCR `packages: write` permission verified; docs access decision documented
**Addresses:** LICENCE-01..04, RELEASE-01..03
**Avoids:** PyPI name-squatting (publish immediately after pending publisher configured), OIDC name mismatch (dry run against test.pypi.org before real index) (Pitfall 10)

### Phase Ordering Rationale

- Phase 1 before Phase 2: Attestation depends on `retriable=True` and retry config flowing through `WorkResponse`. Without Phase 1, attestation round-trip tests see noise from missing retry wiring and the `started_at` field needed in the attestation bundle.
- Phase 2 before Phase 4: The attestation verified/failed/missing badge in the UI requires the `attestation_verified` column to be populated by the orchestrator.
- Phase 3 overlaps with Phase 2: The `env_tag` column can be added to `migration_v14.sql` during Phase 2 execution, shortening Phase 3's schema work.
- Phase 4 partially overlaps Phase 3: Jobs.tsx execution history has no dependency on env_tag; Nodes.tsx env badge waits for Phase 3 API.
- Phase 5 is fully independent: Can be assigned to a parallel workstream at any point.

### Research Flags

Phases requiring careful test-before-merge discipline (not additional external research):
- **Phase 2 (Attestation):** RSA signing pattern is novel in this codebase. All items in the PITFALLS.md "looks done but isn't" checklist must pass before merging: RSA sign/verify round-trip unit test, bundle mutation test (modify exit_code, verify fails), secrets volume isolation test, output scrub order test.
- **Phase 3 (CI/CD Dispatch):** The dispatch response contract (including the 409 behaviour when no eligible node exists) must be confirmed stable before being documented as the CI/CD integration API. Once documented, it cannot change without a breaking-change notice.

Phases with standard patterns (low risk, skip additional research):
- **Phase 1 (Backend wiring):** Scheduler propagation is a two-line addition; `retriable` flag logic is documented in `models.py`. All changes follow patterns already in the codebase.
- **Phase 4 (Frontend UI):** recharts and Radix UI patterns are established in the dashboard. No new dependencies required.
- **Phase 5 (Licence/Release):** PyPI Trusted Publisher prerequisites are documented step-by-step in STACK.md. The release workflow is already correctly configured.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Direct codebase review of `requirements.txt`, `db.py`, `node.py`, `pki.py`, `release.yml`, `pyproject.toml`. No new libraries needed confirmed. RSA key type confirmed in `pki.py` line 380. |
| Features | HIGH | Three major schedulers (Temporal, Rundeck, Google Cloud Scheduler) cross-referenced. Feature gaps verified directly against live code line references. Dependency graph validated against actual DB schema. |
| Architecture | HIGH | All component changes derived from direct codebase inspection. Existing vs. missing implementations confirmed with file and line references. No inference from documentation alone. |
| Pitfalls | HIGH | All pitfalls derived from actual code patterns: RSA key type from `pki.py`, retention gap from `db.py`, thundering herd jitter calculation from `job_service.py` lines 253-254, heartbeat sanitization from lines 388-390. |

**Overall confidence:** HIGH

### Gaps to Address

- **paramiko LGPL-2.1 assessment:** Research recommends confirming whether EE wheel bundling creates a static linking scenario. This requires inspecting the EE packaging process, which was out of scope. Assess during Phase 5 before finalising LEGAL.md. If static linking is found, replace paramiko with `asyncssh` (MIT) — this becomes a Phase 5 implementation task.
- **failed_node_ids retry exclusion:** PITFALLS.md identifies that retry dispatch may repeatedly target the same failing node. Research recommends a `failed_node_ids` JSON column on `Job` but notes it is deferrable if the cluster has multiple eligible nodes per job type. Make an explicit decision during Phase 1 planning: include in v10.0 or log as a deferred MIN issue.
- **Public docs access decision:** Three options (remove CF Access from docs subdomain, publish to GitHub Pages, defer with explicit rationale) require a product decision that is not a technical research question. Must be resolved before Phase 5 closes.

## Sources

### Primary (HIGH confidence)
- `puppeteer/agent_service/db.py` — `ExecutionRecord`, `Node`, `Job`, `ScheduledJob` schemas confirmed directly
- `puppeteer/agent_service/services/job_service.py` — retry logic, env-tag isolation, output scrubbing, `MAX_OUTPUT_BYTES`, zombie reaper, jitter implementation
- `puppets/environment_service/node.py` — RSA key generation (line 380), `build_output_log()`, `report_result()`, heartbeat sanitization
- `puppeteer/agent_service/pki.py` — RSA-2048 key generation confirmed (`rsa.generate_private_key`, public_exponent=65537)
- `puppeteer/agent_service/models.py` — `ResultReport`, `WorkResponse`, `ExecutionRecordResponse` field inventory
- `.github/workflows/release.yml` — PyPI OIDC publish jobs, GHCR multi-arch build confirmed
- [PyPI Trusted Publishers — Creating a project through OIDC](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) — pending publisher prerequisites, name-squatting warning
- [Temporal Retry Policies](https://docs.temporal.io/encyclopedia/retry-policies) — retry field patterns, activity attempt record model
- [Google Cloud Scheduler retry docs](https://docs.cloud.google.com/scheduler/docs/configuring/retry-jobs) — retry field cross-reference
- [Rundeck Executions documentation](https://docs.rundeck.com/docs/manual/07-executions.html) — output capture UX, log size limits (5 MB default)
- [AWS Builders Library — Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) — thundering herd jitter patterns

### Secondary (MEDIUM confidence)
- [Python packaging — License-Expression (PEP 639)](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license) — setuptools >=62.3 requirement (cross-referenced with setuptools changelog)
- `.agent/reports/core-pipeline-gaps.md` — deferred MIN-6 (SQLite subquery delete pattern) directly applicable to output retention pruning SQL

---
*Research completed: 2026-03-17*
*Ready for roadmap: yes*
