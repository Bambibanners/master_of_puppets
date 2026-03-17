# Pitfalls Research

**Domain:** Pull-architecture job scheduler — adding job output capture, runtime attestation, retry policy, environment tags, CI/CD dispatch, and release infrastructure to an existing production system
**Researched:** 2026-03-17
**Confidence:** HIGH (codebase directly inspected — db.py, job_service.py, node.py, pki.py, models.py all read; patterns are verified from the live code, not assumed)

---

## Critical Pitfalls

### Pitfall 1: Attestation Uses the Wrong Key — mTLS Client Key vs. Job Signing Key

**What goes wrong:**
The attestation design (OUTPUT-05..07) requires the node to sign the execution result bundle with its "mTLS client private key." In Axiom, the mTLS client key (`secrets/node-*.key`) is an RSA key (generated via `rsa.generate_private_key` in `pki.py`). The existing job signature verification uses Ed25519. The cryptography library's signing APIs differ by key type: `rsa_key.sign(data, padding, hash_algo)` vs `ed25519_key.sign(data)`. Using the wrong signing call, or failing to specify PKCS1v15/PSS padding for RSA, raises `TypeError` at runtime on the node and results in no attestation bundle being produced — silently, if the exception is swallowed.

The orchestrator also stores the node's cert (`client_cert_pem` column in the `nodes` table) but extracts the public key from the certificate to verify. RSA public key extraction from an X.509 cert requires `cert.public_key()` (returns `RSAPublicKey`), and verification requires `public_key.verify(signature, data, padding, hash_algo)`. If the implementation pattern is copied from the Ed25519 job-signing code (which uses `public_key.verify(sig_bytes, script_bytes)` — two args only, no padding), the RSA verify call will raise `TypeError` on every verification attempt.

**Why it happens:**
The node already has an Ed25519 key for upgrade recipe verification (`secrets/verification.key`). When implementing attestation, it is tempting to reuse this key or to assume the signing pattern is the same. The mTLS client key is RSA; the signing key is Ed25519. These are different objects with different APIs.

**How to avoid:**
- Confirm the key type before implementing: read `secrets/node-*.key` with `serialization.load_pem_private_key`, check `isinstance(key, rsa.RSAPrivateKey)` vs `isinstance(key, ed25519.Ed25519PrivateKey)`.
- For RSA signing, use `key.sign(data, padding.PKCS1v15(), hashes.SHA256())`.
- For RSA verification on the orchestrator, use `public_key.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())` and wrap in try/except `InvalidSignature`.
- Include a unit test on the orchestrator side that loads a known RSA cert PEM (from a test fixture), extracts the public key, and round-trips sign/verify — before the node code is written.

**Warning signs:**
- Attestation code copy-pastes from `signature_service.py` (which uses Ed25519) without adjusting for RSA.
- `public_key.verify(sig_bytes, data_bytes)` with exactly two positional args — this works for Ed25519, raises `TypeError` for RSA.
- Node logs show `TypeError: sign() missing 2 required positional arguments` during result report.

**Phase to address:** Job output capture + attestation phase (OUTPUT-05..07)

---

### Pitfall 2: Output Storage Grows Without Bound — No Retention Policy

**What goes wrong:**
`ExecutionRecord` rows accumulate indefinitely. The `output_log` column is a TEXT field containing JSON — at the 1 MB cap (`MAX_OUTPUT_BYTES = 1_048_576`), each row can consume up to ~1 MB of DB storage. With frequent cron jobs (e.g., every minute × 10 nodes = 14,400 records/day), the `execution_records` table reaches 14 GB in one day at the cap, or ~140 MB/day at an average 10 KB per record. SQLite's WAL journal compounds this. In production Postgres, the table becomes a scan bottleneck even with the existing indexes — the `ix_execution_records_started_at` index spans all nodes and all jobs, so any paginated history query requires filtering the full index range.

**Why it happens:**
The `NodeStats` pruning pattern exists (prune to 60 rows per node in `receive_heartbeat`). No equivalent pruning was added for `execution_records` when the table was designed, because at time of design the output column did not exist. The table was added with four indexes for performance, but no TTL or row cap.

**How to avoid:**
- Add a configurable retention policy: prune `execution_records` older than N days (default: 30 days) via a background task (use the existing APScheduler integration in `scheduler_service.py`).
- Add a per-job-definition cap: keep at most M execution records per `job_guid` (matching the `NodeStats` pruning pattern).
- The pruning SQL for SQLite must not use `DELETE ... WHERE id IN (SELECT ... LIMIT N)` — SQLite requires the `DELETE ... WHERE rowid IN (...)` pattern for subquery deletes (MIN-6 deferred issue applies here too).
- Add a dashboard indicator: show record count and estimated table size in the Admin view so operators know when to tune retention.

**Warning signs:**
- `execution_records` has no scheduled cleanup task at all.
- `output_log` TEXT column with no size cap enforced at the DB level.
- Postgres `pg_table_size('execution_records')` grows unboundedly in load testing.

**Phase to address:** Job output capture phase (OUTPUT-01..04) — address retention before writing the history query UI, not after.

---

### Pitfall 3: Retry Thundering-Herd — All Retrying Jobs Become Eligible Simultaneously

**What goes wrong:**
When a large batch of jobs fails at the same time (e.g., a node disconnects, triggering zombie reaping on 50 jobs), all 50 jobs enter `RETRYING` status with `retry_after` computed as `now + base_delay`. With a 30-second base delay and all jobs reaped in the same zombie-reaper sweep, all 50 jobs become eligible for dispatch at the same instant. The next `pull_work` call from any node finds all 50 at once. All 50 get dispatched, immediately saturating every node's `concurrency_limit`. If the root cause of the original failures was a transient resource pressure, the simultaneous retry batch reproduces the same pressure and fails again — causing cascading retry waves.

The current zombie-reaper code applies `jitter = base_delay * 0.2` (±20% random jitter, see `job_service.py` lines 253-254). This mitigates but does not eliminate thundering herd: with 50 jobs and ±20% of a 30-second window, the effective spread is ±6 seconds — not enough to prevent a surge.

**Why it happens:**
Jitter is applied correctly per-job but the jitter range is proportional to the delay, not to the number of retrying jobs. For small delays (first retry at 30 seconds), 20% jitter is only ±6 seconds. With 50 jobs, the distribution still piles up in a 12-second window.

**How to avoid:**
- For the first retry attempt specifically, add a small random initial offset before the base delay: `initial_offset = random.uniform(0, 30)` added to `retry_after` before the exponential component. This spreads the first retry across a 30-second window regardless of the backoff multiplier.
- Cap the total number of RETRYING jobs that can become eligible in a single `pull_work` scan. The existing query already uses `LIMIT 50` — combine this with the eligibility filter (`retry_after <= now`) so that on a thundering-herd scenario, at most 50 jobs enter the candidate pool per poll cycle. Since nodes poll independently and concurrently, the self-limiting happens naturally.
- Document the jitter recommendation in `JobDefinitionCreate`: "For high-concurrency scheduled jobs, set `backoff_multiplier >= 2.0` and set `timeout_minutes` to prevent indefinite ASSIGNED states."

**Warning signs:**
- Dozens of jobs all have identical `retry_after` timestamps (within a 1-second window).
- Node CPU spikes at regular intervals matching the base retry delay.
- `pull_work` query returns 50 candidates every time a retry wave fires.

**Phase to address:** Retry policy phase (RETRY-01..03)

---

### Pitfall 4: Environment Tag Enforcement Bypassed by Node Self-Reporting

**What goes wrong:**
The current tag system strips `env:` prefixed tags from node-reported heartbeats (see `job_service.py` lines 388-390: `sanitized_tags = [t for t in hb.tags if not t.startswith("env:")]`). This correctly prevents node self-escalation on reported tags. However, if `ENVTAG-01` is implemented by storing the env tag on the `Node` record at enrollment time (from the JOIN_TOKEN or the enrollment request) but the heartbeat sanitization is not reviewed, a developer might add env-tag reporting back to the heartbeat payload as a convenience during development and forget to strip it. The sanitization is not tested explicitly.

Additionally: if environment tags are stored in the existing `operator_tags` column (separate from `tags`), the `_get_effective_tags()` method returns `operator_tags` when set and ignores `tags` entirely. This means an env tag set at enrollment via `operator_tags` will be correctly enforced, but an env tag set via the API on the `tags` column would be silently ignored — confusing operators who set the env tag via the "wrong" column.

**Why it happens:**
The env tag feature adds a new semantic to an existing multi-purpose column. The distinction between `tags` (node-reported, sanitized) and `operator_tags` (admin-set, authoritative) is correct architecturally but is not enforced by the data model — both are `TEXT` columns storing JSON lists. There is no DB-level constraint or API-level validation preventing an env tag from appearing in the wrong column.

**How to avoid:**
- Add a dedicated `env_tag` column to the `Node` table (nullable `String`, `ALTER TABLE` migration required for existing DBs). This separates the semantics entirely from the general tag columns.
- At enrollment (`/api/enroll`), accept `env_tag` as a JOIN_TOKEN field or enrollment request field (operator-configurable per deployment, not node-self-reported).
- In `pull_work`, enforce env tag matching using the `env_tag` column, not the tags columns. Do not mix env tag logic with capability or general tag logic.
- Keep the existing `env:` prefix strip in heartbeat sanitization as a defense-in-depth measure.

**Warning signs:**
- Env tag is stored in the same `tags` or `operator_tags` column as general tags, parsed by `startswith("env:")`.
- No dedicated `env_tag` column in the Node schema.
- No test that verifies a node with `env_tag=PROD` does not receive a job targeted at `env_tag=DEV`.

**Phase to address:** Environment tags phase (ENVTAG-01..04)

---

### Pitfall 5: Retry Dispatch Assigns to the Same Node That Just Failed

**What goes wrong:**
When a job fails and enters `RETRYING` status, `node_id` is set to `None` (see `job_service.py` line 745). This correctly clears the assignment so any eligible node can pick it up on the next poll. However, the `pull_work` job selection query does not exclude the node that previously failed the job. If the failure was node-specific (OOM kill, missing capability, transient file system error), retrying on the same node reproduces the failure. This is especially problematic for zombie-reaped jobs: the zombie reaper clears `node_id` to `None`, but if only one node is eligible (based on tags and capabilities), that node picks up the retry and zombies again.

**Why it happens:**
The retry mechanism correctly implements the general case (retry on any eligible node) but there is no concept of "node affinity exclusion" — a per-attempt record of which nodes have already failed this job. The `ExecutionRecord` table stores `node_id` per attempt, so the data to implement exclusion exists but is not used in `pull_work`.

**How to avoid:**
- For jobs with `max_retries > 0`, add a `failed_node_ids` JSON column to `Job` (or derive it from `ExecutionRecord` at dispatch time). During `pull_work` node selection, exclude nodes whose ID appears in this list.
- Fallback: if all eligible nodes are in the exclusion list, allow reassignment to the least-recently-failed node (preventing permanent deadlock when there is only one eligible node).
- If adding a new column is not acceptable in the initial retry phase, at minimum exclude the most-recently-failed node: store the last-failed node ID in `job.node_id` during the retry state transition, and skip the job if the polling node matches. Clear it after a successful assignment to a different node.

**Warning signs:**
- Retry telemetry shows the same node_id in every `ExecutionRecord` attempt for a failing job.
- Jobs with `max_retries=3` reach `DEAD_LETTER` without ever being attempted on a second node.
- No node exclusion logic in `pull_work` for RETRYING jobs.

**Phase to address:** Retry policy phase (RETRY-01..03)

---

### Pitfall 6: `create_all` Does Not Add New Columns to Existing Tables

**What goes wrong:**
Every v10.0 feature requires new DB columns:
- Output capture: attestation fields on `ExecutionRecord` (`attestation_bundle`, `attestation_verified`, `script_hash`, `stdout_hash`, `stderr_hash`) — the current `ExecutionRecord` has none of these.
- Environment tags: `env_tag` on `Node`.
- Retry: `failed_node_ids` on `Job` (if implementing node exclusion).
- Release: no schema changes, but CI/CD dispatch API response fields need confirmation.

`Base.metadata.create_all` only creates tables that do not exist. It never adds columns to existing tables. Any new column added to an ORM model will be silently ignored on an existing deployment — no error, no warning, the column simply does not exist. Queries using that column then fail at runtime with a DB error ("no such column"), not at startup.

**Why it happens:**
This is the documented constraint of the no-Alembic pattern (noted in CLAUDE.md: "Adding new columns to existing deployed DBs requires manual ALTER TABLE"). The pattern is known but requires discipline to apply consistently for every new column across every feature.

**How to avoid:**
- Create a single `migration_v14.sql` file alongside the v10.0 work (following the existing `migration_v10.sql`..`migration_v13.sql` pattern).
- List every new column, new table, and new index in this file using `ADD COLUMN IF NOT EXISTS` (Postgres) / `ALTER TABLE IF NOT EXISTS` (SQLite-compatible pattern requires conditional approach via `PRAGMA table_info`).
- Run the migration file against both SQLite (dev) and Postgres (prod) in CI before merging any v10.0 changes.
- The startup `create_all` handles fresh deployments; the migration SQL handles upgrades.

**Warning signs:**
- New ORM columns added in `db.py` with no corresponding `migration_v14.sql` entry.
- Local dev works (fresh SQLite from `create_all`) but Docker Compose with persistent volume fails at runtime.
- CI only tests against fresh DB (no migration path test).

**Phase to address:** First v10.0 phase that touches the schema — define `migration_v14.sql` upfront and add to it incrementally.

---

### Pitfall 7: Attestation Bundle Is Not Truly Tamper-Evident Without All Fields

**What goes wrong:**
OUTPUT-05 defines the attestation bundle as: `script_hash + stdout_hash + stderr_hash + exit_code + start_timestamp + node_cert_serial`. If any of these fields is omitted from the signed payload, the attestation bundle loses tamper-evidence for that field. The most common omission is `exit_code`: it is a small integer and feels like it "doesn't need" hashing. But an attacker who intercepts a result report (a compromised network segment, or a compromised orchestrator DB) can change `exit_code` from 1 to 0 (turning a failure into a success) without invalidating the signature — if `exit_code` is not in the signed bundle.

Similarly, if the bundle does not include the `node_cert_serial`, an orchestrator with multiple enrolled nodes cannot distinguish whether the signature came from the correct node or from another enrolled node whose private key was compromised.

**Why it happens:**
Bundle fields get chosen pragmatically ("what do we hash?") rather than threat-modelling-first. The script hash and output hashes are obvious; the exit code and cert serial are less obvious but equally necessary.

**How to avoid:**
The canonical bundle format must be deterministically serialized before signing. Recommended approach:
```
bundle_bytes = json.dumps({
    "script_sha256": ...,     # hex
    "stdout_sha256": ...,     # hex (SHA256 of raw stdout bytes)
    "stderr_sha256": ...,     # hex
    "exit_code": int,
    "start_ts": ISO8601,       # from job.started_at as assigned by orchestrator, not node clock
    "cert_serial": hex(int),   # node's cert serial number
}, sort_keys=True, separators=(',', ':')).encode('utf-8')
signature = key.sign(bundle_bytes, ...)
```

`sort_keys=True` is mandatory: JSON key ordering is not guaranteed across Python versions, and a reordered bundle would produce a different hash and fail verification.

**Warning signs:**
- Bundle construction uses f-string concatenation rather than deterministic JSON serialization.
- `exit_code` is not in the signed bundle.
- `cert_serial` is not in the signed bundle.
- No test that verifies modifying `exit_code` in the stored bundle causes verification to fail.

**Phase to address:** Runtime attestation phase (OUTPUT-05..07)

---

### Pitfall 8: CI/CD Dispatch API Returns 202 Before the Job Is Verified as Dispatched

**What goes wrong:**
The CI/CD dispatch endpoint (ENVTAG-04) creates a job and returns `{"job_id": ..., "status": "PENDING", "node_assigned": null}` immediately. A CI pipeline polling this endpoint expects `node_assigned` to populate within some timeout. If no eligible node exists (wrong env tag, no matching capabilities, all nodes at concurrency limit), the job stays PENDING indefinitely. The pipeline either times out and marks the build as failed, or loops forever.

The current `create_job` function returns immediately after DB commit without checking node availability. This is correct for async dispatch but makes the CI/CD endpoint unsuitable as-is for synchronous pipeline integration without explicit status polling guidance.

**Why it happens:**
The pull architecture means the orchestrator never knows when (or if) a node will pick up a job at creation time. This is a fundamental property of the architecture — not a bug. But it means a "dispatch and wait" CI/CD pattern requires explicit polling and timeout handling that must be documented and ideally supported by the API response structure.

**How to avoid:**
- The dispatch endpoint response must include: `job_id`, `status`, `node_assigned` (null until assigned), and a `poll_url` field pointing to `GET /jobs/{job_id}` so pipelines know where to poll.
- Add a `max_wait_seconds` optional query parameter: the endpoint does a short-poll (e.g., waits up to 30 seconds for PENDING → ASSIGNED transition) before returning. This trades a slightly longer initial request for a simpler pipeline integration.
- Alternatively: document clearly that pipelines must poll `GET /jobs/{job_id}` until `status == "ASSIGNED"` or timeout. Include the polling pattern in the API reference and the CI/CD guide.
- Return 409 (not 202) if no eligible node exists at dispatch time (check node availability before creating the job).

**Warning signs:**
- Dispatch endpoint returns immediately with `status: PENDING` and no polling guidance in the response.
- No timeout handling documented for CI pipelines.
- No test that verifies the dispatch endpoint returns a non-null `poll_url`.

**Phase to address:** Environment tags + CI/CD dispatch phase (ENVTAG-03..04)

---

### Pitfall 9: Output Log Truncation Happens After Secret Scrubbing — Allows Secret Leakage

**What goes wrong:**
The current `report_result` logic (job_service.py lines 690-706) scrubs secrets first, then truncates the output_log. This is correct. However, when output capture is extended (OUTPUT-01..03), if a developer reverses the order — truncating first, then scrubbing — secrets that appear near the end of a long output may survive in the stored log: the truncation removed the scrubbing candidate from the list but the secrets were already written to an intermediate buffer or transmitted to the frontend. The risk is specifically in streaming or incremental output capture implementations where lines are buffered and flushed piecemeal.

For attestation specifically: the `stdout_hash` in the attestation bundle must hash the raw (pre-scrub) bytes, not the post-scrub bytes. If the hash is computed post-scrub, the verification on an independent verifier (using the raw stdout bytes from the job container) will always fail — because the verifier computes the hash of the original output, not the redacted version.

**Why it happens:**
The scrub-then-truncate order is not documented as a security invariant. When output capture code is refactored or extended, the ordering is not preserved. The attestation hash-on-raw vs hash-on-scrubbed distinction is subtle and easy to get wrong.

**How to avoid:**
- Compute the attestation hashes (`stdout_sha256`, `stderr_sha256`) on the raw output bytes from the node, before any scrubbing or truncation. The hashes go into the bundle for attestation purposes.
- Store only the scrubbed, truncated output in `execution_records.output_log`.
- Add a comment in `report_result` explicitly marking the ordering constraint: `# ORDER: hash raw → scrub → truncate → store`.
- Test: verify that a job with `[REDACTED]` in its stored output still produces a valid attestation bundle when the verifier uses the raw (pre-scrub) output hash.

**Warning signs:**
- Attestation hash computed after `entry["line"].replace(secret, "[REDACTED]")`.
- No comment marking the scrub order as a security invariant.
- Truncation code appears before the scrubbing loop.

**Phase to address:** Runtime attestation phase (OUTPUT-05..07), cross-check during output capture phase (OUTPUT-01..04)

---

### Pitfall 10: PyPI Trusted Publisher Fails if GitHub Org/Project Names Don't Match Exactly

**What goes wrong:**
PyPI Trusted Publisher OIDC configuration requires the GitHub org name, repository name, workflow filename, and environment name to match exactly — case-sensitive. If the `axiom-laboratories` org is created with any variation in capitalization, or the workflow file is renamed, the OIDC trust relationship silently rejects the publishing attempt with a generic authentication failure, not an informative "trust mismatch" error.

Additionally: the PyPI project name (`axiom-sdk`) must be registered before the Trusted Publisher relationship can be configured. If the project does not yet exist on PyPI when the relationship is configured, PyPI's "pending publisher" feature must be used (added in 2023). If the workflow runs before the pending publisher is set up, it will fail at the upload step, not at the OIDC step, producing a misleading error.

**Why it happens:**
The distinction between "pending publisher" (project doesn't exist yet) and "standard publisher" (project already exists) is not obvious from the PyPI UI. Most guides describe the standard flow. The GHCR workflow uses `ghcr.io/axiom-laboratories/axiom` as the image name — this requires the org to exist on GitHub and for the workflow to push with the right permissions (`packages: write`) before the image name is accepted.

**How to avoid:**
- Use PyPI's pending publisher feature (configure the trust relationship before the first publish, even before the `axiom-sdk` project exists).
- Exact matching checklist: GitHub org = `axiom-laboratories`, repo = `master_of_puppets` (or whatever it will be named), workflow file = exact filename in `.github/workflows/`, environment name = exact string used in the workflow `environment:` field.
- Test the OIDC flow with a dry-run `--repository testpypi` against test.pypi.org before targeting the real PyPI index.
- For GHCR: verify `packages: write` permission is in the workflow's `permissions:` block; the Actions workflow must explicitly request this permission (it is not inherited from `contents: write`).

**Warning signs:**
- Workflow uses `environment: production` but PyPI publisher is configured with `environment: release`.
- `axiom-sdk` PyPI project name not pre-registered (even as a placeholder release).
- No `permissions: packages: write` in the GHCR workflow job.

**Phase to address:** Release infrastructure phase (RELEASE-01..02)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store env_tag in existing `tags` column with `env:` prefix | No schema change required | Confused with general tags; operator_tags override semantics apply; harder to enforce isolation | Only if migration is impossible (it isn't here) |
| Skip `failed_node_ids` exclusion in first retry implementation | Simpler initial implementation | Jobs retry on the same failing node; persistent failures hit DEAD_LETTER without trying other nodes | Acceptable if cluster has only 1 eligible node per job type; otherwise harmful |
| Hash post-scrub stdout for attestation | Simpler code path (single pass) | Attestation always fails independent verification; attestation bundle is meaningless | Never — defeats the purpose of attestation |
| Attestation bundle uses string concatenation instead of deterministic JSON | Faster to implement | Fails on Python version differences in dict ordering, float repr, or unicode normalization | Never — deterministic serialization costs 2 lines |
| No output retention policy at launch | Deferred complexity | DB storage grows unboundedly; history queries degrade; SQLite dev DBs become unusable | Only for initial testing deployments with < 100 job runs |
| CI/CD dispatch returns immediately without polling guidance | Simpler endpoint | Pipeline integrations timeout or loop forever waiting for job assignment | Never — document the polling pattern at minimum |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| mTLS client key signing (attestation) | Copy Ed25519 `key.sign(data)` call for RSA key | RSA: `key.sign(data, padding.PKCS1v15(), hashes.SHA256())` — three arguments |
| mTLS cert public key extraction (attestation verify) | `cert.public_key().verify(sig, data)` two-arg form | RSA: `public_key.verify(sig, data, padding.PKCS1v15(), hashes.SHA256())` — four arguments |
| PyPI Trusted Publisher OIDC | Configure standard publisher (project must exist) | Use "pending publisher" for new project; exact case-sensitive name matching required |
| GHCR image publish | Workflow runs without `permissions: packages: write` | Explicitly declare `permissions` block in the workflow job; `contents: read` alone is not enough |
| Environment tag enforcement | Store `env_tag` via node heartbeat (self-reported) | Set env_tag at enrollment only (operator-controlled), strip `env:` prefix from heartbeat sanitization |
| Attestation bundle for independent verification | Hash post-scrub/post-truncation output | Hash raw output bytes before any processing; store raw hashes in attestation bundle |
| Retry backoff on first attempt | Use `retry_count - 1` in exponent | At retry_count=1 (first retry): `30 * 2.0 ** 0 = 30s` — correct; but add random initial offset to prevent synchronized retry waves |
| SQLite subquery delete (output retention) | `DELETE WHERE id IN (SELECT ... LIMIT N)` | SQLite requires `DELETE WHERE rowid IN (SELECT rowid ...)` — test on SQLite, not just Postgres |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `execution_records` unbounded growth | History queries slow; full-table scans in SQLite; Postgres autovacuum struggling | Scheduled retention pruning via APScheduler; keep 30 days or 1000 records per job | At ~10K records in SQLite dev; at ~10M rows in Postgres without partitioning |
| Attestation verification on every history page load | `/jobs/{id}/history` triggers N cert-public-key extractions for N records | Compute and store `attestation_verified` at write time (in `report_result`); never re-verify on read | Immediately if verification is synchronous in the read path |
| `RETRYING` job scan includes all jobs regardless of `retry_after` | `pull_work` query returns 50 candidates but 48 are RETRYING too early, wasting selection loop iterations | Index on `(status, retry_after)` — already partially handled by the existing query filter; add a composite index | At >100 concurrent RETRYING jobs |
| Output log JSON parse on every list_jobs call | `list_jobs` parses `output_log` TEXT for every row in the result set | `list_jobs` should NOT include output_log; only include it in `GET /jobs/{id}/executions/{exec_id}` | At >50 jobs in a single page |
| Attestation bundle stored as raw bytes in TEXT column | UTF-8 encoding of binary signature bytes corrupts base64-encoded data | Store attestation bundle as base64 encoded string, not raw bytes | On first non-ASCII byte in the signature (which happens regularly with RSA/SHA256 output) |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Attestation private key (node mTLS key) accessible to job scripts | A malicious job script reads `../secrets/node-*.key` and exfiltrates the attestation key | Ensure job containers run with `--read-only` filesystem and no volume mount to the secrets directory; test with a job that tries to read the key |
| CI/CD dispatch API endpoint has no rate limiting | Automated pipelines submit thousands of jobs per minute; DB and nodes overwhelmed | Add per-API-key rate limiting (e.g., 60 dispatch calls/minute) at the CI/CD endpoint; return 429 with `Retry-After` header |
| Environment tag enforcement via general tags column | A node self-reports `env:PROD` in its heartbeat tags, bypassing the sanitization if sanitization is removed or missed | Use a dedicated `env_tag` column; never mix env semantics with general tag matching |
| Attestation `missing` (not verified) treated same as `verified` in audit log | Orchestrator silently accepts unattested results; attestation adds no security value | `attestation_verified = "missing"` must be flagged in the audit log; operators must be able to query for unattested results |
| CI/CD dispatch API accepts unauthenticated requests | Any caller can submit jobs to PROD environment | CI/CD endpoint must require service principal auth (`mop_` API key prefix); no anonymous dispatch |
| Release workflow publishes on every push to main | Accidental version bump publishes an unreviewed release to PyPI | Publish workflow triggers only on `push: tags: ['v*']`; never on branch push or PR merge |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Retry state "attempt N of M" not shown on in-progress jobs | Operator sees job as ASSIGNED with no indication it is a retry attempt | Dashboard Jobs view shows `retry N/M` badge when `retry_count > 0`; link to all attempt records |
| Execution history shows raw JSON output_log | Operators see `[{"t": "...", "stream": "stdout", "line": "..."}]` — unreadable | Render output_log as a terminal-style view with stream colour coding (stdout = normal, stderr = yellow); use a monospace font |
| Attestation `verified/failed/missing` shown as a status string only | Operators don't know what to do with a failed attestation | Show attestation failure with a direct link to the runbook: "Attestation failed — see Security Runbook: Tampered Result" |
| Environment tag field not shown in node enrollment flow | Operators enroll nodes without setting env_tag; all nodes end up in the default environment | Nodes view enrollment form must include env_tag dropdown (DEV/TEST/PROD/custom); default shown as "none (untagged)" |
| CI/CD dispatch response contains `status: PENDING` permanently | Pipeline waits forever; no indication that no eligible node exists | Add `eligible_nodes_available: true/false` to dispatch response; if false, include `reason: "No nodes with env_tag=PROD and capability X"` |

---

## "Looks Done But Isn't" Checklist

- [ ] **Attestation round-trip:** Sign a known bundle with an RSA key, extract the cert's public key, and verify in the orchestrator — all in a unit test that runs in CI. Not tested = not working.
- [ ] **Attestation with all fields:** Modify `exit_code` in the stored bundle and verify that re-verification fails. Modify `cert_serial` and verify it fails. If either mutation passes verification, the bundle format is missing those fields.
- [ ] **Retry node exclusion:** Submit a job to a single eligible node; make it fail; verify the second attempt targets a different node (if one exists). If the same node is retried, node exclusion is not implemented.
- [ ] **Output retention pruning:** Insert 1000 execution records for a single job, trigger the retention job manually, verify the count drops to the configured cap. Test on both SQLite and Postgres.
- [ ] **Environment tag isolation:** Create a job targeting `env_tag=PROD`; enroll a DEV node; verify the job is never dispatched to the DEV node. The test must wait through at least 3 poll cycles.
- [ ] **Env tag self-escalation blocked:** Send a heartbeat from a DEV node with `env:PROD` in the tags; verify the node's stored tags do not include `env:PROD` after the heartbeat.
- [ ] **CI/CD dispatch with no eligible node:** Call the dispatch endpoint with `env_tag=PROD` when no PROD node is enrolled; verify the response is 409 (not 202) or includes `eligible_nodes_available: false`.
- [ ] **PyPI Trusted Publisher dry run:** Run the release workflow against test.pypi.org before touching the real index. Verify OIDC token exchange succeeds in the log. A successful dry run is the only proof the configuration is correct.
- [ ] **Output scrubbing order invariant:** Submit a job with a secret in its payload; verify the stored `output_log` contains `[REDACTED]`; verify the attestation hash matches the pre-scrub output. Both must pass in the same test.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wrong key type in attestation (RSA vs Ed25519) | MEDIUM | Fix signing/verification code; all existing attestation bundles in DB are invalid — mark them as `attestation_verified = "failed"` retroactively; future executions produce correct bundles |
| Output table grew unbounded before retention added | HIGH (if Postgres; MEDIUM for SQLite) | Run manual `DELETE FROM execution_records WHERE started_at < NOW() - INTERVAL '30 days'`; add index-guided pagination to avoid lock; then deploy the scheduled retention job |
| Attestation hashes computed post-scrub | HIGH | All existing attestation bundles are non-independently-verifiable; fix the hash computation; existing bundles must be marked `attestation_verified = "legacy_unverifiable"`; no retroactive fix possible |
| Thundering herd retry wave detected in production | LOW | Set `retry_after` on all RETRYING jobs to `NOW() + random(0, 300)` via one-time SQL update; deploy the per-attempt initial offset fix |
| PyPI publish failed due to OIDC name mismatch | LOW | Correct the publisher configuration on PyPI (takes 5 minutes); re-run the workflow |
| Env tag not enforced (wrong column) | MEDIUM | Add `env_tag` column via migration; backfill from existing operator_tags using string parsing; update dispatch enforcement to use new column; test isolation |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| RSA vs Ed25519 attestation key type | Runtime attestation phase (OUTPUT-05..07) | Unit test: RSA sign/verify round-trip with a test cert fixture |
| Output table unbounded growth | Job output capture phase (OUTPUT-01..04) — add retention before history UI | `SELECT COUNT(*) FROM execution_records` after load test; must not grow without bound |
| Retry thundering herd | Retry policy phase (RETRY-01..03) | Check `retry_after` timestamps on a batch of failed jobs — spread > 30 seconds required |
| Env tag self-escalation bypass | Environment tags phase (ENVTAG-01..04) | Heartbeat test: send `env:PROD` in tags, verify not stored |
| Retry to same failing node | Retry policy phase (RETRY-01..03) | Submit job to a failing single-eligible node; verify DEAD_LETTER without retrying same node when another eligible node exists |
| `create_all` missing new columns | First schema-change phase (whichever comes first) | Run migration SQL against a copy of the production DB snapshot; verify no "no such column" errors on startup |
| Attestation bundle incomplete fields | Runtime attestation phase (OUTPUT-05..07) | Bundle mutation test: modify exit_code, verify verification fails |
| CI/CD dispatch without polling guidance | CI/CD dispatch phase (ENVTAG-04) | Poll integration test: dispatch job, poll until ASSIGNED or timeout; no infinite loop |
| PyPI Trusted Publisher OIDC mismatch | Release infrastructure phase (RELEASE-01) | Dry run against test.pypi.org before touching real index |
| Output scrubbing order inversion | Output capture phase (OUTPUT-01..04) — reinforce in attestation phase | Unit test: job with secret → stored log shows REDACTED → attestation hash matches raw bytes |
| Attestation private key accessible to job scripts | Runtime attestation phase (OUTPUT-05..07) | Job container must have no volume mount to secrets/ directory; test with a job attempting key file read |
| CI/CD endpoint unauthenticated | CI/CD dispatch phase (ENVTAG-04) | Anonymous HTTP call to dispatch endpoint must return 401 |

---

## Sources

- Direct codebase inspection: `puppeteer/agent_service/db.py` (ExecutionRecord, Node, Job schemas), `puppeteer/agent_service/services/job_service.py` (zombie reaper, retry logic, output scrubbing, `MAX_OUTPUT_BYTES = 1_048_576`), `puppeteer/agent_service/pki.py` (RSA key generation — `rsa.generate_private_key`), `puppets/environment_service/node.py` (heartbeat sanitization, key file locations), `puppeteer/agent_service/models.py` (ResultReport, ExecutionRecordResponse)
- Python `cryptography` library — RSA signing API: `cryptography.hazmat.primitives.asymmetric.padding.PKCS1v15`, three-argument `verify()` vs Ed25519 two-argument `verify()` — verified from library source
- PyPI Trusted Publisher documentation — pending publisher flow for new projects: https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
- Thundering herd in retry systems — jitter strategies: AWS Architecture Blog "Exponential Backoff and Jitter" (2015, timeless pattern)
- Known deferred issue MIN-6 (SQLite NodeStats pruning compat with subquery delete) — documented in `.agent/reports/core-pipeline-gaps.md`, directly applicable to output retention
- Job status machine in `job_service.py` lines 736-784 — retry state transitions inspected for node-exclusion gap
- Heartbeat sanitization pattern (`env:` prefix strip) — `job_service.py` lines 388-390

---
*Pitfalls research for: Axiom v10.0 — adding output capture, attestation, retry policy, environment tags, CI/CD dispatch to existing pull-architecture job scheduler*
*Researched: 2026-03-17*
