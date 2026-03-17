# Feature Research

**Domain:** Production job scheduler / orchestration platform — v10.0 commercial release features
**Researched:** 2026-03-17
**Confidence:** HIGH (Temporal, Rundeck, Google Cloud Scheduler, AWS docs verified via official sources; patterns cross-referenced across three schedulers)

---

## Context: What This Milestone Covers

This research is scoped to **v10.0 Axiom Commercial Release** — adding production-grade observability,
cryptographic attestation, retry policy, environment targeting, licence compliance, and release
infrastructure to a mature, deployed orchestration platform.

The platform already has:
- mTLS node enrollment, Ed25519 job signing, container-isolated execution
- RBAC (admin/operator/viewer), OAuth device flow, JWT auth, service principals
- Cron-scheduled job definitions (APScheduler), Foundry image builder, Smelter Registry
- Pull-model nodes, capability matching, node targeting, AuditLog, Staging view
- `axiom-push` CLI, job lifecycle (DRAFT/ACTIVE/DEPRECATED/REVOKED), full documentation site

The six v10.0 feature areas are researched below. Each area maps to a set of requirements
from REQUIREMENTS.md (OUTPUT-01..07, RETRY-01..03, ENVTAG-01..04, LICENCE-01..04, RELEASE-01..03).

---

## Feature Area 1: Job Output Capture + Execution History (OUTPUT-01..04)

### Table Stakes (operators expect these from any production scheduler)

| Feature | Why Expected | Complexity | Axiom Notes |
|---------|--------------|------------|-------------|
| **Stdout + stderr capture per execution** | Without this, operators cannot diagnose failures. Every serious scheduler (Rundeck, Temporal, Jenkins, Airflow) captures output. No capture = product feels like a demo. | MEDIUM | Node must capture subprocess stdout/stderr at `runtime.py` level and POST them to orchestrator on completion alongside exit code. New `ExecutionRecord` DB table. |
| **Exit code stored and surfaced** | Non-zero exit code is the primary signal that a job failed. Operators need this to distinguish "ran but errored" from "never ran". | LOW | Already tracked implicitly for job status; needs explicit per-execution storage alongside stdout/stderr. |
| **Per-execution timestamps (start + end)** | Duration is a first-class monitoring signal. Operators set SLA alerts on execution time. "Finished at" is table stakes. | LOW | Store `started_at` and `completed_at` on each `ExecutionRecord`. Duration is derived, not stored. |
| **Execution history per job definition** | "Show me all runs of this cron job in the last 7 days" is the most common operator query. Without it, you cannot tell if intermittent failures are trending worse. | MEDIUM | Query `ExecutionRecord` by `job_definition_id`, paginated, sorted descending by `started_at`. |
| **Execution history per node** | "What jobs ran on this node?" identifies noisy nodes and helps diagnose node-specific failures. | LOW | Query `ExecutionRecord` by `node_id`. Re-uses the same table. |
| **Inline output viewer in dashboard** | Clicking into a run and seeing stdout/stderr inline is the minimum UX. Having to call an API to get logs is not acceptable for a product with a dashboard. | MEDIUM | Modal or expandable panel in Jobs view and JobDefinitions view. Requires a `GET /executions/{id}/output` endpoint or inline in execution response. |
| **Output size limit + truncation** | Runaway jobs can produce gigabytes of output. Unlimited storage for logs will fill the DB. Rundeck defaults to 5MB per execution with configurable `truncate` or `halt` action. | LOW | Set a soft limit (configurable, default 64KB or 1MB). Truncate from the tail (preserve first lines where the failure usually appears). Store a `output_truncated: bool` flag on the record. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Script hash stored per execution** | Operators can verify that the script executed was exactly the version they signed — even months later. No other open-source scheduler does this by default. | LOW | `script_hash` (SHA-256 of the script bytes) already exists on job definitions. Copy to `ExecutionRecord` at dispatch time. Requires zero extra work if stored at dispatch. |
| **Linked attempt records (retries)** | When retry policy is active, all attempts for a single "logical run" are grouped under a parent `JobRun` record. Operators see "attempt 1 of 3" rather than three disconnected executions. | HIGH | See retry policy feature area. Requires parent `JobRun` → child `ExecutionRecord` relationship. |
| **Execution timeline view** | A sparkline or bar chart showing execution durations over time for a job definition. Regression detection at a glance. | HIGH | Deferred — nice-to-have; v11.0 candidate. Existing node sparklines (recharts) are a precedent. |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Live log streaming (WebSocket)** | "I want to watch a job run in real-time" sounds essential. | Requires persistent WebSocket from orchestrator → node or node → orchestrator during execution, which breaks the pull model. Nodes are stateless between polls; mid-execution streaming would require the node to push, opening an inbound connection or a long-lived out-poll, both of which undermine the security and NAT-traversal design. | Post-execution output capture covers 95% of operator needs. The REQUIREMENTS.md explicitly defers live streaming to a future milestone. A polling endpoint (`GET /executions/{id}/status`) every 5 seconds is sufficient while waiting. |
| **Structured log parsing (JSON log fields)** | "Extract specific fields from JSON output" | This requires knowing the output format of every job, which Axiom deliberately does not — jobs are arbitrary scripts. Parsing would require per-job schema configuration, which is a different product. | Store raw stdout/stderr as text. Let operators grep or process downstream. The attestation bundle provides structured integrity data. |
| **Log shipping to external systems (Elasticsearch, Loki)** | "Push logs to our SIEM" | Log shipping integrations are maintenance-heavy, version-sensitive, and require credentials in the orchestrator. The scope creeps indefinitely. | Store output in the DB per execution. Export via the API. Operators can ETL to their SIEM using `GET /executions`. This is v2+ territory. |

---

## Feature Area 2: Runtime Attestation (OUTPUT-05..07)

### Table Stakes

| Feature | Why Expected | Complexity | Axiom Notes |
|---------|--------------|------------|-------------|
| **Attestation stored per execution** | If you ship attestation, every execution must produce one. Partial attestation (some executions signed, others not) is worse than none — it creates false confidence. | MEDIUM | Store attestation bundle bytes and `verification_status` (`verified` / `failed` / `missing`) on `ExecutionRecord`. |
| **Verification result in execution record** | Operators need to see "attestation verified" in the dashboard without having to export and manually verify. The verification status must be computed server-side on receipt. | MEDIUM | On receipt of each execution report, verify the attestation signature against the stored node certificate. Store `attestation_verified: bool`. |
| **Exportable attestation bundles** | Compliance use cases require offline proof that a specific script ran on a specific node at a specific time with a specific output. This is the core value of attestation. | LOW | Serve raw signed bundle bytes via `GET /executions/{id}/attestation`. No special storage needed beyond the existing execution record. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Node cert serial in attestation bundle** | Ties the attestation cryptographically to the enrolled node identity, not just a key pair. An attacker who steals a signing key but does not have a valid cert cannot produce a trusted attestation. | LOW | The cert serial is available from `node.client_cert_pem` at attestation verification time. Include it in the bundle at node side; verify against the stored cert at orchestrator side. |
| **Attestation covers stdout hash, not just exit code** | Exit code alone can be spoofed or misreported. Hashing stdout + stderr output and including those hashes in the signed bundle means the operator can verify not just that the job "ran" but that the output is authentic. | LOW | SHA-256 of stdout bytes and stderr bytes, included in the signed JSON bundle alongside the script hash, exit code, and timestamps. |
| **Tamper-evident chain: signing key → cert → attestation** | The Ed25519 signing requirement (for script authorship) plus the mTLS client cert (for node identity) plus the attestation signature (for execution proof) creates a three-link chain of cryptographic evidence. No other open-source scheduler offers this. | HIGH | The implementation is LOW complexity per link; the HIGH complexity is testing the full chain end-to-end and documenting the verification workflow for operators. |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Attestation blocking execution** | "Don't execute if attestation will fail" | Attestation is a post-execution verification mechanism, not a pre-execution gate. A pre-execution gate would require the orchestrator to predict the attestation before the job runs, which is circular. | Attestation failure should be a dashboard alert and audit log event. Policy enforcement (fail the job if attestation fails verification) is an operator-configured option, not a default. |
| **Hardware-based TEE attestation (SGX, TrustZone)** | "Use hardware root of trust" | TEE attestation requires specialised hardware on every node, which is incompatible with Axiom's design goal of running on commodity servers, homelab hardware, and Docker containers. | The mTLS client certificate issued by Axiom's Root CA provides a software-based chain of trust that is sufficient for Axiom's stated use cases. Hardware attestation is v3+ territory. |
| **SLSA provenance format** | "Produce SLSA L2/L3 attestations" | Full SLSA compliance requires build provenance infrastructure beyond the execution attestation bundle. REQUIREMENTS.md explicitly defers SLSA to a future milestone. | Axiom's custom attestation bundle provides the functionally equivalent evidence. SLSA-format export can be added later as a bundle transformer. |

---

## Feature Area 3: Retry Policy (RETRY-01..03)

### Table Stakes

Production schedulers (Temporal, Google Cloud Scheduler, AWS EventBridge, APScheduler) all provide
configurable retry policies. Operators expect this from any scheduler that runs critical workloads.

| Feature | Why Expected | Complexity | Axiom Notes |
|---------|--------------|------------|-------------|
| **Maximum retry count** | "Try 3 times, then give up" is the minimum operators need. No retry count = every job is either run-once or runs forever. | MEDIUM | `max_retries: int` on `ScheduledJob`/`JobDefinition`. Default: 0 (no retries, backward-compatible). |
| **Fixed-interval backoff** | Simple constant wait between retries. Required for jobs that fail due to transient resource contention (e.g., "DB is briefly locked"). | LOW | `backoff_strategy: "fixed"`, `backoff_seconds: int`. Implemented in `job_service.py` retry dispatch logic. |
| **Exponential backoff** | Standard in every production scheduler. Google Cloud Scheduler, Temporal, AWS all default to exponential with a cap. Avoids thundering-herd on retry storms. | LOW | `backoff_strategy: "exponential"`, `backoff_base_seconds`, `backoff_max_seconds`. Formula: `min(base * 2^attempt, max)`. Verified pattern from Temporal (base=1s, coefficient=2.0, cap=100s) and Google Cloud Scheduler (min=5s, max=3600s). |
| **Each attempt = separate execution record** | Operators need to see individual attempt outputs to diagnose why retry 1 failed differently from retry 2. A single merged record obscures this. | MEDIUM | Introduce `JobRun` parent record (logical run) → `ExecutionRecord` children (individual attempts). `attempt_number` on each child. Aligns with how Temporal separates activity attempts. |
| **Retry state visible in dashboard** | "Attempt 2 of 3, waiting 30s before retry" must be surfaced in the Jobs view. Without this, operators have no way to know whether a stuck job is retrying or dead. | MEDIUM | `JobRun.status` values: `pending`, `running`, `retrying`, `succeeded`, `failed_exhausted`. Display in Jobs view with attempt counter. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Retry only on non-zero exit code (not timeout)** | Some jobs are timeout-sensitive (e.g., release deploys) and should not retry after a timeout. Others should always retry. Separating the two triggers gives operators fine-grained control. | MEDIUM | `retry_on_failure: bool` (non-zero exit), `retry_on_timeout: bool` (node heartbeat timeout). Both default true. |
| **Non-retryable exit code list** | Temporal's `non_retryable_errors` list is a well-understood pattern. For scripts, the equivalent is "if exit code is 2 (usage error), do not retry." | LOW | `non_retryable_exit_codes: list[int]` on job definition. If the exit code matches, exhaust retries immediately rather than waiting out the full policy. |
| **Per-definition retry policy override** | Global default retry policy is a convenience; per-job override is required for mixed criticality workloads (critical backups retry 5x; health checks retry 0x). | LOW | Retry policy fields live on `ScheduledJob` table. Ad-hoc job dispatch can also specify a retry policy in the request body. |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Infinite retries by default** | "We want jobs to eventually succeed" | Temporal defaults to unlimited retries, but Temporal is a durable workflow engine where retries are the primary execution model. In Axiom, a job that has failed 50 times is a broken job, not a pending one. Infinite retries fill the execution history table, generate noise, and mask real failures. | Default to 0 retries (no retry). Operators opt in per job definition. Maximum configurable value should be bounded (e.g., 10) with a clear admin escape hatch. |
| **Retry across different nodes** | "If node A fails, retry on node B" | Node failover retry requires the job to be idempotent on any node and for the orchestrator to guarantee the first attempt has stopped before the retry starts. In the pull model, a timed-out node may still be executing when the retry dispatches — creating two concurrent executions of the same job. | Retry on the same node (or any available matching node via normal capability matching). The existing node heartbeat timeout already gates this: once a node is considered timed out, its cert is revocable. The retry uses normal dispatch, not node-specific targeting. |
| **Dead-letter queue** | "Failed retries should go to a DLQ for manual review" | DLQ is a message-queue pattern, not a scheduler pattern. Building a DLQ in a relational DB requires a separate table, a consumer process, and an operator workflow. | The `JobRun.status = 'failed_exhausted'` state in the dashboard IS the dead-letter view. Operators review failed exhausted runs from the existing Jobs/JobDefinitions views. A filtered query endpoint achieves the same UX with zero new infrastructure. |

---

## Feature Area 4: Environment Tags + CI/CD Targeting (ENVTAG-01..04)

### Table Stakes

| Feature | Why Expected | Complexity | Axiom Notes |
|---------|--------------|------------|-------------|
| **Environment tag on nodes (DEV/TEST/PROD)** | Every infrastructure tool with environment awareness uses this model. Kubernetes uses namespace-per-environment. GitLab CI uses environment names. Without this, operators must maintain separate Axiom instances per environment — an antipattern. | LOW | `environment_tag: str` on `Node` table. Configurable via `ENV_TAG` environment variable in node compose file. Enrolls and stores the tag at the node level. No new DB table. |
| **Environment filter in job targeting** | Being able to say "run this job only on PROD nodes" is the primary use case. Combined with existing capability matching, this enables full environment-segregated job dispatch. | LOW | `target_environment: str` (optional) on `ScheduledJob` and ad-hoc dispatch. `job_service.py` filters candidate nodes by `environment_tag` after capability matching. |
| **Environment tag visible in Nodes dashboard** | Operators must be able to identify which environment each node belongs to at a glance. Missing from the UI = operators have no situational awareness during incidents. | LOW | Add `env` badge column to `Nodes.tsx` node table. Filter control in the header bar. Already have `capabilities` display as precedent. |
| **CI/CD dispatch API endpoint** | The entire point of environment tags is enabling automated pipeline promotion (DEV → TEST → PROD). Without a documented API endpoint that pipeline runners can call, the feature has no CI/CD integration story. | MEDIUM | `POST /jobs/dispatch` with `environment_tag` parameter, returning `{"job_run_id": ..., "node_id": ..., "status": ...}` structured JSON. Document as the CI/CD integration point. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Custom environment tag strings (not enum-locked)** | DEV/TEST/PROD is the common case. But enterprise teams use `staging`, `canary`, `dr-recovery`, `customer-demo`. Locking to an enum forces workarounds and reduces adoption. | LOW | Store as `VARCHAR` with no DB enum constraint. Validate non-empty at enrollment. Provide DEV/TEST/PROD as suggested defaults in the docs. |
| **Environment-scoped operator permissions (future)** | Operators in DEV should not be able to dispatch to PROD. This is a natural extension of the existing RBAC model. | HIGH | DEFER to v11.0 — requires extending the permission model with environment scope. Note in docs as a roadmap item. |
| **Structured CI/CD response for pipeline gates** | CI/CD runners (GitHub Actions, GitLab CI, Jenkins) need to know if the dispatched job succeeded before proceeding to the next pipeline stage. A synchronous poll or a webhook callback makes Axiom a first-class pipeline citizen. | MEDIUM | `POST /jobs/dispatch` returns immediately with job_run_id. CI/CD caller polls `GET /job-runs/{id}/status` until terminal state. Document the polling pattern explicitly in docs. Webhook callbacks deferred to v11.0. |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Separate Axiom instance per environment** | "DEV and PROD should be completely isolated" | Separate instances multiply operational overhead (separate DBs, separate CAs, separate dashboards, separate config management). The security case for total separation is addressed by environment tags + RBAC — a PROD-only operator role cannot dispatch to DEV nodes by policy. | Environment tags on a single instance with RBAC scope is the correct pattern. Document the security rationale explicitly. Separate instances remain a valid operator choice but should not be the only path. |
| **Environment promotion pipelines built into Axiom** | "Axiom should manage DEV→TEST→PROD promotion workflows" | Promotion logic is business-specific. Building it into the scheduler means Axiom takes on DAG dependencies, conditional triggers, and approval gates — all deferred features. This is scope creep for v10.0. | Axiom provides the environment-targeted dispatch API. The CI/CD pipeline (GitHub Actions, etc.) owns the promotion logic. Axiom is a tool called by the pipeline, not the pipeline itself. |

---

## Feature Area 5: Licence Compliance (LICENCE-01..04)

### Table Stakes

For any open-source or dual-licence commercial product, these are not optional.

| Feature | Why Expected | Complexity | Axiom Notes |
|---------|--------------|------------|-------------|
| **`License-Expression` in pyproject.toml** | PEP 639 (accepted, Python 3.12+) mandates `License-Expression` using SPDX identifiers as the canonical licence field. PyPI displays this. Package managers consume it. | LOW | `License-Expression = "Apache-2.0"` for CE; `"LicenseRef-Proprietary"` for EE wheel. One-line addition to `pyproject.toml`. |
| **NOTICE file for attribution requirements** | Apache-2.0 itself requires a NOTICE file listing attributions. CC-BY-4.0 packages (caniuse-lite) require attribution. Missing this is an IP compliance failure. | LOW | Enumerate all direct dependencies with attribution requirements. caniuse-lite (CC-BY-4.0) is confirmed in REQUIREMENTS.md. `pip-licenses` can automate the enumeration. |
| **certifi MPL-2.0 assessment in LEGAL.md** | MPL-2.0 has a file-level copyleft: any modifications to MPL-licensed files must be released. Since certifi is used read-only (CA bundle), no source modification occurs — the assessment is the compliance act. | LOW | One documented paragraph in LEGAL.md. REQUIREMENTS.md has the analysis: "read-only CA bundle, no source modification, obligations satisfied." |
| **paramiko LGPL-2.1 assessment** | LGPL-2.1 is compatible with Apache-2.0 for dynamic linking. If EE bundles paramiko statically, the bundled copy falls under LGPL's copyleft. Assessment documents which case applies. | MEDIUM | Confirm dynamic-only import (inspect import path, check wheel packaging). If dynamic: document and close. If static or bundled: replace with `asyncssh` (MIT) to avoid LGPL obligation. |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **GPL dependencies anywhere in the stack** | "GPL libraries are sometimes the best option" | Any GPL dependency in the CE codebase contaminates the dual-licence model. GPL is copyleft-viral: it requires all combined works to be GPL. This would void the EE proprietary licence. | Mandate GPL-clean dependency tree as a contribution requirement. Use `pip-licenses --fail-on="GPL"` in CI. Document in CONTRIBUTING.md. |
| **LGPL in EE statically bundled wheel** | Bundling ships one artifact to customers | If paramiko or any LGPL library is compiled/bundled statically into the EE wheel, the wheel contains LGPL code that must be releasable under LGPL terms — which contradicts the proprietary EE licence. | Ensure all LGPL dependencies remain dynamically linked (installed separately, not bundled). If bundling is required, replace with MIT alternatives first. |

---

## Feature Area 6: Release Infrastructure (RELEASE-01..03)

### Table Stakes

For a product declaring itself ready for commercial/open-source adoption, these are the minimum
release hygiene requirements.

| Feature | Why Expected | Complexity | Axiom Notes |
|---------|--------------|------------|-------------|
| **PyPI Trusted Publisher (OIDC)** | Long-lived PyPI API tokens are a credential management burden and a leak risk. OIDC Trusted Publishers eliminate long-lived secrets by exchanging short-lived GitHub Actions tokens. This is PyPI's recommended approach since 2023. | LOW | Requires: (1) `axiom-laboratories` GitHub org, (2) PyPI project `axiom-sdk`, (3) trust configuration linking the repo + workflow file + environment. The workflow already uses `pypa/gh-action-pypi-publish` — only the org/project creation is blocking. |
| **GHCR multi-arch image publishing** | `linux/amd64` and `linux/arm64` are both required for modern infrastructure. arm64 (Raspberry Pi, Apple Silicon, AWS Graviton) is standard in homelabs and enterprise cloud. An amd64-only image will generate issues from day one. | LOW | The existing release workflow already targets multi-arch. The only blocker is activating it with the correct org and registry path. |
| **Documented public docs decision** | Open-source adoption requires discoverable documentation. The current docs site is CF Access protected. A documented decision (expose publicly or provide an explicit rationale for deferral) is required for v10.0 completeness. | LOW | Three options: (1) Remove CF Access from the docs subdomain, (2) Publish docs to GitHub Pages as a separate deployment, (3) Defer with explicit rationale (e.g., "docs contain internal deployment instructions"). Pick one and document it. |

### Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **GitHub community health files (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY.md)** | Open-source projects without these have lower contribution rates and lower perceived maturity. GitHub surfaces a "Community Standards" checklist; missing items are visible to potential contributors. | LOW | CONTRIBUTING.md and CHANGELOG already exist (v9.0). Add SECURITY.md (responsible disclosure process) and CODE_OF_CONDUCT.md (Contributor Covenant is the standard). |
| **Signed releases (sigstore/cosign)** | Cryptographically signed PyPI packages and OCI images are increasingly expected. The Axiom brand is built on cryptographic security — unsigned releases are a reputational inconsistency. | MEDIUM | Use `sigstore` for PyPI (built into `pypa/gh-action-pypi-publish` as opt-in). Use `cosign` for GHCR. Add to release workflow. Low implementation cost relative to brand alignment value. |

### Anti-Features

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Docker Hub publishing (in addition to GHCR)** | "Wider reach" | Docker Hub rate limits on pulls are a support burden. Hub requires a separate login, separate credentials, separate namespace management. GHCR is free for public packages, integrated with GitHub Actions OIDC, and has no pull rate limits for public images. | Publish to GHCR only. Document the pull path clearly. Docker Hub publishing can be added later if community demand warrants it. |
| **Manual release process** | "We'll tag and push manually for now" | Manual releases introduce human error, inconsistent artifact naming, and unsigned packages. Any v10.0 release process that is not automated is a regression from the CI/CD pipelines already built in v9.0. | The existing release workflow handles everything automatically on version tag push. Only the org/project prerequisites are missing. Do not bypass it. |

---

## Feature Dependencies

```
[ExecutionRecord (DB table)]
    └──required-by──> [Job output capture (OUTPUT-01, OUTPUT-02)]
    └──required-by──> [Execution history queries (OUTPUT-03, OUTPUT-04)]
    └──required-by──> [Attestation storage (OUTPUT-05, OUTPUT-06)]
    └──required-by──> [Retry attempt records (RETRY-02)]

[JobRun (parent record)]
    └──required-by──> [Retry policy (RETRY-01, RETRY-02)]
    └──enhances──>    [Execution history (groups attempts)]
    └──requires──>    [ExecutionRecord]

[Attestation signature verification]
    └──requires──>  [ExecutionRecord (to store verification_status)]
    └──requires──>  [node.client_cert_pem (stored at enrollment — existing, Sprint 8)]
    └──requires──>  [Node signs bundle with mTLS client private key (node-side change)]
    └──enables──>   [Exportable attestation bundles (OUTPUT-07)]

[environment_tag on Node]
    └──required-by──> [Job targeting by environment (ENVTAG-02)]
    └──required-by──> [CI/CD dispatch API (ENVTAG-04)]
    └──required-by──> [Nodes view env filter (ENVTAG-03)]

[axiom-laboratories GitHub org + PyPI project]
    └──required-by──> [PyPI Trusted Publisher (RELEASE-01)]
    └──required-by──> [GHCR activation (RELEASE-02)]

[LEGAL.md + NOTICE file]
    └──required-by──> [Licence compliance (LICENCE-01..04)]
    └──independent-of──> [all feature code changes]
```

### Dependency Notes

- **ExecutionRecord must come first:** All observability and attestation features build on this
  table. Phase ordering must put the DB schema + node-side reporting before the dashboard views.

- **JobRun introduces a schema change:** The current model has `Job` records (ad-hoc dispatches)
  and `ScheduledJob` definitions. Retry policy requires a new `JobRun` concept (a logical
  execution instance, potentially spanning multiple `ExecutionRecord` attempts). This is a
  non-trivial data model change and should be in its own phase.

- **Attestation depends on node-side code change:** The node (`puppets/environment_service/node.py`)
  must load its mTLS client private key and sign the execution bundle before reporting results.
  This is the only feature that requires changes to the node agent code. Node agent changes
  require rebuilding any Foundry-built images that bundle the agent.

- **Licence compliance is independent of all code changes:** LEGAL.md, NOTICE, and pyproject.toml
  updates can be done in parallel with any code feature phase. They have no implementation
  dependencies. They do have a release-order dependency: must be complete before PyPI publish.

- **Release infrastructure is a prerequisite for PyPI/GHCR, not for feature work:** The org
  and project creation unblocks publishing but does not block feature development. Can be
  done in parallel.

---

## v10.0 Scope Definition

### Deliver in v10.0

- [ ] **Job output capture (ExecutionRecord)** — stdout/stderr/exit code/timestamps stored per execution — OUTPUT-01, OUTPUT-02
- [ ] **Execution history queries** — per job definition, per node; paginated — OUTPUT-03, OUTPUT-04
- [ ] **Dashboard output viewer** — inline stdout/stderr in Jobs view — OUTPUT-03
- [ ] **Runtime attestation** — node signs bundle; orchestrator verifies; bundles exportable — OUTPUT-05, OUTPUT-06, OUTPUT-07
- [ ] **Retry policy** — max retries + fixed/exponential backoff; JobRun parent + ExecutionRecord children; dashboard retry state — RETRY-01, RETRY-02, RETRY-03
- [ ] **Environment tags** — `ENV_TAG` on nodes; job targeting; Nodes view filter; CI/CD dispatch API — ENVTAG-01, ENVTAG-02, ENVTAG-03, ENVTAG-04
- [ ] **Licence compliance** — LEGAL.md, NOTICE, pyproject.toml `License-Expression`, paramiko assessment — LICENCE-01, LICENCE-02, LICENCE-03, LICENCE-04
- [ ] **Release infrastructure** — axiom-laboratories org + PyPI Trusted Publisher + GHCR activation + docs access decision — RELEASE-01, RELEASE-02, RELEASE-03

### Explicitly Deferred (not v10.0)

- [ ] **Live log streaming (WebSocket)** — breaks pull model; post-execution output is sufficient (REQUIREMENTS.md explicit deferral)
- [ ] **Log shipping (Elasticsearch, Loki)** — v2+ integration feature; API export is sufficient
- [ ] **Environment-scoped RBAC** — requires permission model extension; v11.0
- [ ] **SLSA provenance format** — custom attestation bundle covers the need; REQUIREMENTS.md explicit deferral
- [ ] **DAG job dependencies + conditional triggers** — v11.0 in REQUIREMENTS.md
- [ ] **Docker Hub publishing** — GHCR only for v10.0
- [ ] **Signed releases (sigstore/cosign)** — valuable but not blocking commercial release; v10.x

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| ExecutionRecord DB + node reporting | HIGH | MEDIUM | P1 — everything else blocks on this |
| Execution history API + dashboard viewer | HIGH | MEDIUM | P1 |
| Environment tags + job targeting | HIGH | LOW | P1 |
| CI/CD dispatch API | HIGH | LOW | P1 |
| Retry policy (max_retries + backoff) | HIGH | MEDIUM | P1 |
| JobRun parent record | HIGH | MEDIUM | P1 — required for retry |
| Runtime attestation (node + orchestrator) | HIGH | HIGH | P1 — Axiom's security differentiator |
| Licence compliance (LEGAL.md + NOTICE) | HIGH | LOW | P1 — required before PyPI |
| PyPI Trusted Publisher activation | HIGH | LOW | P1 — requires org creation |
| GHCR multi-arch activation | HIGH | LOW | P1 — requires org creation |
| Output viewer in dashboard | HIGH | MEDIUM | P1 |
| Nodes view env tag display + filter | MEDIUM | LOW | P2 |
| Non-retryable exit code list | MEDIUM | LOW | P2 |
| Public docs access decision | MEDIUM | LOW | P2 |
| Attestation export API | MEDIUM | LOW | P2 |
| Signed releases (cosign/sigstore) | MEDIUM | MEDIUM | P3 |
| Live log streaming | HIGH | HIGH | DEFER — breaks pull model |
| Log shipping integrations | LOW | HIGH | DEFER |

**Priority key:**
- P1: Must ship in v10.0 to deliver the milestone
- P2: Should ship in v10.0; adds depth but not blocking
- P3: Nice to have; add if time permits or in v10.x

---

## Competitor Feature Analysis

How production job schedulers handle these feature areas:

| Feature Area | Temporal | Rundeck | Google Cloud Scheduler | Axiom v10.0 Approach |
|---|---|---|---|---|
| **Output capture** | Full output per activity attempt, stored in event history | Stdout/stderr per execution, 5MB default cap, configurable truncate/halt | HTTP response body captured (not stdout) | DB-stored stdout/stderr per ExecutionRecord, 64KB default cap, truncation flag |
| **Execution history** | Full event history per workflow, exportable to S3 | Execution list per job, filterable by date/status, API-accessible | Cloud Logging integration | Queryable per job definition and per node, paginated API endpoint |
| **Retry policy** | Initial interval, backoff coefficient, max interval, max attempts, non-retryable errors — per activity | Max retries configurable, fixed or exponential — per job step | retryCount (max 5), minBackoff, maxBackoff, maxDoublings, maxRetryDuration | max_retries, backoff_strategy (fixed/exponential), backoff_base_seconds, backoff_max_seconds, non_retryable_exit_codes |
| **Attempt records** | ActivityTaskStarted events suppressed until completion to reduce noise; final history shows all attempts | Each attempt is a separate execution record with own logs | No sub-attempt visibility (HTTP level only) | JobRun parent + ExecutionRecord children with attempt_number |
| **Attestation** | Not provided (workflow identity via mTLS/auth, not execution-level signing) | Not provided | Not provided | Ed25519 + mTLS client cert signed bundle; SHA-256 of script + stdout + stderr + exit code + timestamp |
| **Environment tags** | Namespace-based worker routing (task queues by environment) | Node tags/attributes for targeting | No native concept (use Cloud Run environments) | `environment_tag` on nodes, `target_environment` on job definitions, CI/CD dispatch API |
| **CI/CD API** | SDK-based dispatch, HTTP polling for completion | Rundeck API `POST /api/1/job/{id}/run`, returns `execution.id` for polling | `POST /v1/projects/-/jobs/{id}:run` | `POST /jobs/dispatch` with environment_tag, returns job_run_id for polling |
| **Licence compliance** | Temporal CE: MIT; Cloud: proprietary | Rundeck CE: Apache-2.0; PD: proprietary | Google proprietary | Apache-2.0 CE + proprietary EE; PEP 639 License-Expression; NOTICE file |

**Key differentiator vs peers:** Axiom's runtime attestation (execution-level cryptographic proof
combining the mTLS node identity cert, Ed25519 script signing, and SHA-256 output hashes) has no
equivalent in Rundeck, Temporal, or any cloud scheduler. It is uniquely positioned for regulated
industries, audit-heavy environments, and air-gapped security-first deployments.

---

## Sources

- [Rundeck Executions documentation](https://docs.rundeck.com/docs/manual/07-executions.html) — output capture UX patterns, log size limits (5MB default), truncate/halt behaviour — HIGH confidence
- [Google Cloud Scheduler — Retry jobs](https://docs.cloud.google.com/scheduler/docs/configuring/retry-jobs) — retry policy fields: retryCount (max 5), minBackoffDuration, maxBackoffDuration, maxDoublings — HIGH confidence
- [Temporal Retry Policies](https://docs.temporal.io/encyclopedia/retry-policies) — initial interval, backoff coefficient, max interval, max attempts, non-retryable errors; activity attempt event history suppression pattern — HIGH confidence
- [AWS — Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) — full jitter vs equal jitter; idempotency requirement for retry with backoff — HIGH confidence
- [PyPI Trusted Publishers documentation](https://docs.pypi.org/trusted-publishers/) — OIDC setup, GitHub Actions integration, no long-lived tokens — HIGH confidence
- [GitLab CI — Environments](https://docs.gitlab.com/ci/environments/) — DEV/TEST/PROD environment pattern; same-artifact promotion; environment name conventions — HIGH confidence
- [Kubernetes Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/) — env label patterns, selector-based targeting — HIGH confidence
- [Rundeck config reference — execution log limits](https://docs.rundeck.com/docs/administration/configuration/config-file-reference.html) — `rundeck.execution.logs.output.limit = 5MB`, `limitAction: truncate` — HIGH confidence
- [Temporal — Idempotency and durable execution](https://temporal.io/blog/idempotency-and-durable-execution) — idempotency key patterns for retry with separate attempt records — MEDIUM confidence

---

*Feature research for: Axiom v10.0 — production job scheduler commercial release features*
*Researched: 2026-03-17*
