# Phase 25: Runbooks & Troubleshooting - Research

**Researched:** 2026-03-17
**Domain:** MkDocs Material documentation authoring — operational runbooks
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Symptom header format:**
- Primary headers (H2): observable state — what the operator sees in the dashboard or terminal, not internal component names. Examples: "Node shows Offline but container is running", "Job stuck in Queued for more than 5 minutes"
- Secondary headers (H3): exact error message — when a distinctive log line or UI error message identifies the specific cause, it appears as an H3 under the observable symptom H2.
- Cluster grouping by failure area: Each runbook page uses H2 clusters (e.g., "Enrollment Failures", "Heartbeat Loss", "Cert Errors") with individual symptoms nested as H3s under the cluster.
- Quick-reference jump table at the top of every page: one column = symptom, other column = anchor link to the section.

**Diagnostic depth per symptom:**
- Linear structure per symptom: Root cause (2-sentence explanation) → numbered recovery steps → "Verify it worked" step (command + expected output) → "If still failing" escalation note.
- Multi-cause symptoms: each cause gets its own H3 sub-section.
- No branching decision trees.
- Log snippets in code blocks: signing errors, dispatch errors, and cert errors include the exact log line.
- End pattern: every symptom section ends with a Verify step then "If the issue persists after these steps, [open an issue / check logs with X command]".

**FAQ structure:**
- One unified FAQ page (`runbooks/faq.md`) — single searchable page.
- Format: Bold question as H3 header, 2–4 sentence answer, code snippet where needed. No collapsible blocks.
- Required gotchas:
  - Blueprint packages must use `{"python": [...]}` dict format — not a plain list
  - `EXECUTION_MODE=direct` required when running Docker-in-Docker
  - JOIN_TOKEN is base64-encoded JSON containing the Root CA PEM — not a plain API key
  - `ADMIN_PASSWORD` in `.env` only seeds the admin account on first startup
- Operational how-tos: "How do I reset a node without re-enrolling?", "Why does my scheduled job not run at the expected time?" (timezone), "Can I run jobs without Ed25519 signing?" (no)

**Cross-linking strategy:**
- Minimal repetition + clear links. No full procedure repetition.
- Runbooks cross-link to FAQ where applicable.

### Claude's Discretion

- Exact number of FAQ entries beyond the four required gotchas and three how-to examples
- Section ordering within each runbook cluster beyond the required cluster names
- Exact wording of the 2-sentence root cause explanations
- Whether the Foundry runbook clusters mirror node/job clusters or are Foundry-specific

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RUN-01 | Node troubleshooting guide covers enrollment failures, heartbeat loss, and cert errors (symptom-first) | Node error messages catalogued from node.py and main.py; cert mechanics from mtls.md; cross-link targets identified |
| RUN-02 | Job execution troubleshooting covers dispatch failures, signing errors, and timeout patterns | Exact error strings extracted from node.py execute_task(); job status lifecycle from job_service.py; signing failure log lines confirmed |
| RUN-03 | Foundry troubleshooting covers build failures, Smelt-Check failures, and registry issues | foundry_service.py error paths catalogued; Smelter enforcement modes documented; push failure patterns identified |
| RUN-04 | FAQ addresses the top operator questions (common misconfigurations, gotchas) | Required gotchas confirmed from MEMORY.md, core-pipeline-gaps.md, and validated code paths; operational how-tos scoped |
</phase_requirements>

---

## Summary

Phase 25 produces four MkDocs pages under `docs/docs/runbooks/`: `nodes.md`, `jobs.md`, `foundry.md`, and `faq.md`. All prior documentation infrastructure is complete — the nav stub is in place in `mkdocs.yml`, admonitions are configured, and the cross-link targets (mtls.md, mop-push.md, foundry.md) exist with confirmed anchor text. This phase is pure content authoring with no new infrastructure.

The research establishes the full catalogue of failure modes, exact log messages, and error strings visible to operators across the three subsystems. The symptom-first structure is fully locked in CONTEXT.md. The primary work for the planner is mapping each requirement to a set of symptom sections with known root causes and recovery steps drawn from the actual codebase.

**Primary recommendation:** Write each runbook page in stub-first order (nav entries already exist; add stub files, then fill content) to maintain `mkdocs build --strict` compliance throughout. All four pages can be written in parallel since they have no content dependencies on each other.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| MkDocs Material | configured | Doc site rendering | Already deployed; all extensions configured |
| admonition | configured | `!!! warning / danger / tip` blocks | Used in Phases 22–24 |
| pymdownx.details | configured | Collapsible detail blocks | Available but CONTEXT.md says no collapsible blocks in runbooks |
| tables | configured | Markdown tables | Standard extension already active |

No new libraries or dependencies are introduced in this phase. All tooling is inherited from Phases 20–24.

**Installation:** None required.

---

## Architecture Patterns

### Recommended File Structure
```
docs/docs/runbooks/
├── index.md          # Update stub — overview + links to all four pages
├── nodes.md          # RUN-01: Node troubleshooting (enrollment, heartbeat, certs)
├── jobs.md           # RUN-02: Job execution troubleshooting (dispatch, signing, timeouts)
├── foundry.md        # RUN-03: Foundry troubleshooting (builds, Smelt-Check, registry)
└── faq.md            # RUN-04: Unified FAQ
```

`mkdocs.yml` nav section update required:
```yaml
- Runbooks:
  - Overview: runbooks/index.md
  - Node Troubleshooting: runbooks/nodes.md
  - Job Execution: runbooks/jobs.md
  - Foundry: runbooks/foundry.md
  - FAQ: runbooks/faq.md
```

### Pattern 1: Runbook Page Structure (Locked)
**What:** Every runbook page follows this top-level layout.
**When to use:** All four runbook pages.

```markdown
# [Subsystem] Troubleshooting

[1-2 sentence orientation: what this page covers, who it's for]

## Quick Reference

| Symptom | Section |
|---------|---------|
| [Observable state] | [#anchor-link] |
...

---

## [Cluster: e.g., Enrollment Failures]

### [Symptom or exact error message]

[Root cause — exactly 2 sentences explaining why this happens.]

**Recovery steps:**

1. [Step one]
2. [Step two]
...

**Verify it worked:**

```bash
[command]
```

Expected output: `[what success looks like]`

If the issue persists after these steps, [open an issue / run `docker logs <container>`].
```

### Pattern 2: Symptom → H3 Exact Error Message
**What:** When a specific log line uniquely identifies the cause, that log line is the H3 header.
**Example:**
```markdown
## Enrollment Failures

### `❌ Enrollment Failed: [Errno 111] Connection refused`

Root cause: The node cannot reach the orchestrator at the configured AGENT_URL...
```

### Pattern 3: Multi-Cause Symptoms
**What:** One observable symptom (H2 or H3) with multiple distinct root causes, each as a sub-H3.
```markdown
### Node shows Offline but container is running

#### Cause 1: Heartbeat thread waiting for cert files
...

#### Cause 2: Certificate revoked
...
```

### Anti-Patterns to Avoid
- **Decision trees:** No "if X then Y else Z" branching. Use linear steps; the verify step is the branch point.
- **Full procedure repetition:** Never copy cert rotation steps from mtls.md. Cross-link instead.
- **Collapsible blocks:** No `???` pymdownx.details in runbooks — bad for crisis reading.
- **Component-name headers:** Never "PKI Service Error" as a header. Use "Node cannot enroll".

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Anchor links | Custom HTML ids | Standard Markdown H2/H3 (MkDocs auto-generates anchors) | MkDocs slugifies headers automatically |
| Search | Custom index | Built-in lunr search | Already configured; air-gap safe |
| Jump tables | JavaScript | Simple Markdown table with `[text](#anchor)` links | Works in MkDocs without plugins |

**Key insight:** All navigation features operators need (jump tables, cross-links, search) work with plain Markdown. No custom plugins or scripts are needed.

---

## Common Pitfalls

### Pitfall 1: Anchor Mismatch in Jump Tables
**What goes wrong:** Jump table links like `[Symptom](#node-shows-offline)` 404 because MkDocs slugifies differently than expected.
**Why it happens:** MkDocs Material lowercases and replaces spaces with hyphens, strips special characters. Emoji, backticks, and punctuation in headers change the anchor.
**How to avoid:** Test anchors locally after writing headers. Avoid backticks, emoji, and punctuation in H2/H3 headers used as jump targets. Use a plain text version of the header as the anchor.
**Warning signs:** MkDocs build with `--strict` does not catch broken internal anchors — they silently 404 at runtime.

### Pitfall 2: Admonition Inside Numbered Steps
**What goes wrong:** A `!!! warning` block inside a numbered list breaks the list numbering — MkDocs resets the counter.
**Why it happens:** Admonitions are block-level elements; inserting them in a list resets the list state.
**How to avoid:** Place admonitions before or after the numbered list, not inside it. If a warning must precede a specific step, number the steps manually (use `1.`, `2.`, etc. and accept the reset, or place the warning after the block).

### Pitfall 3: mkdocs build --strict Does Not Catch Runtime 404s
**What goes wrong:** `mkdocs build --strict` passes but cross-links to anchors in other pages are broken at runtime.
**Why it happens:** Strict mode only catches missing page references, not missing anchors within pages.
**How to avoid:** When cross-linking to an anchor (e.g., `../security/mtls.md#cert-rotation`), verify the target header exists and produces that anchor. Check source files directly.

### Pitfall 4: Log Line Accuracy
**What goes wrong:** Runbook shows a log line slightly different from what the code actually emits — operators search for the exact string and don't find the runbook section.
**Why it happens:** Log format was changed after the runbook was written, or the line was paraphrased.
**How to avoid:** Copy exact log strings from source code. All log strings in this research are lifted directly from the committed codebase.

---

## Failure Mode Catalogue

This section is the primary reference for planner task creation. All error strings are verified against committed source code.

### Node Subsystem Failures

**Enrollment Failures** (cluster: RUN-01)

| Symptom | Log line | Root cause | Source |
|---------|----------|-----------|--------|
| Container exits immediately at startup | `❌ Enrollment Failed: <exception>` | JOIN_TOKEN malformed, AGENT_URL unreachable, or cert files from previous enrollment still present | node.py:420 |
| Enrollment fails: connection refused | `❌ Enrollment Failed: [Errno 111] Connection refused` | AGENT_URL points to wrong host/port | node.py:420 |
| Enrollment fails: SSL error | `❌ Enrollment Failed: SSL: CERTIFICATE_VERIFY_FAILED` | JOIN_TOKEN CA does not match the server's TLS cert; VERIFY_SSL mismatch | node.py:420 |
| Node enrolls but appears as duplicate in dashboard | (no log line — observable from dashboard) | Old `node-*.crt` files in secrets volume causing `_load_or_generate_node_id()` to reuse stale ID that already exists in DB | node.py:54-58 |
| `Token payload missing 't' or 'ca'` | `Token payload missing 't' or 'ca'` | JOIN_TOKEN is not an Enhanced Token (base64 JSON with `t` and `ca` keys) — may be a legacy/plain token | node.py:346 |

**Heartbeat Loss** (cluster: RUN-01)

| Symptom | Log line | Root cause | Source |
|---------|----------|-----------|--------|
| Node goes Offline in dashboard after container restart | `[Heartbeat] Failed: <exception>` | Heartbeat thread cannot find cert files — waits in loop until cert exists | node.py:218-220 |
| Node status never returns Online after cert rotation | (dashboard: node stays Offline) | Old cert revoked but `secrets/` volume was not cleared — node reuses revoked cert | node.py:57, mtls.md#cert-rotation |
| Node shows TAMPERED in dashboard | (dashboard badge; log: `🚨 TAMPER DETECTED on node <id>`) | Node reported a capability not in `expected_capabilities` — zero-trust guard triggered | job_service.py:421-433 |

**Certificate Errors** (cluster: RUN-01)

| Symptom | Log line | Root cause | Source |
|---------|----------|-----------|--------|
| Node gets HTTP 403 on work/pull | (node log: no explicit 403 print — connection drops silently) | Node certificate is revoked; `/work/pull` returns 403 for revoked certs | main.py (enroll/work routes) |
| Node gets HTTP 403 on enroll | (no explicit print) | Certificate already revoked; `RevokedCert` table check blocks re-enrollment | main.py enroll route |
| Work pull blocked with concurrency 0 | Node receives `concurrency_limit: 0` in config | Node is REVOKED template or TAMPERED — orchestrator sends concurrency=0 to halt execution | job_service.py:184, 200 |

### Job Subsystem Failures

**Dispatch Failures** (cluster: RUN-02)

| Symptom | Log line | Root cause | Source |
|---------|----------|-----------|--------|
| Job stuck in Queued / PENDING indefinitely | (dashboard: status stays PENDING) | No node has the required tags, capabilities, or memory budget to accept the job | job_service.py:302-360 |
| Job status BLOCKED | (dashboard: status BLOCKED) | Job has `depends_on` and dependency job has not yet COMPLETED | job_service.py:127-130 |
| Job status CANCELLED | `🚫 Job <guid> cancelled because upstream <guid> failed` | Upstream dependency failed — cancellation propagated | job_service.py:644 |
| Job status DEAD_LETTER | `Job <guid> exhausted all <N> retries and failed terminally.` | Job exceeded `max_retries` — alert created | job_service.py:752-758 |
| Job status ZOMBIE_REAPED | (execution record: `ZOMBIE_REAPED`) | Job was ASSIGNED but node did not complete it within zombie timeout (default: 30 min) | job_service.py:239-260 |

**Signing Errors** (cluster: RUN-02)

| Symptom | Log line | Root cause | Source |
|---------|----------|-----------|--------|
| Job status SECURITY_REJECTED — signature failed | `❌ Signature Verification FAILED for Job <guid>: <exception>` | Script was signed with a different key than the public key registered in Signatures; or script was modified after signing | node.py:524 |
| Job status SECURITY_REJECTED — verification key missing | `❌ CRITICAL: Verification Key missing. Cannot verify signature.` | Node cannot fetch verification key from `/verification-key` endpoint — usually a connectivity issue at startup | node.py:511 |
| Job status SECURITY_REJECTED — missing script or signature | `Missing script or signature` (in job result) | Job payload was submitted without a signature field — mop-push was not used, or the signature was dropped | node.py:506 |

**Timeout Patterns** (cluster: RUN-02)

| Symptom | Timeout value | Root cause | Source |
|---------|-------------|-----------|--------|
| Job moves from ASSIGNED to FAILED after ~30 minutes | zombie_timeout_minutes (default: 30) | Node stopped responding / crashed mid-execution; zombie reaper reclaims the job | job_service.py:37-40 |
| Script job exits with error: Execution timed out | 30-second hardcoded subprocess timeout | Script ran longer than 30 seconds in `run_python_script()` direct subprocess path | node.py:474 |
| Job stays ASSIGNED, node never reports result | (no log) | Node container OOM killed (memory_limit hit) or network partition | job_service.py zombie reaper |

### Foundry Subsystem Failures

**Build Failures** (cluster: RUN-03)

| Symptom | Log line | Root cause | Source |
|---------|----------|-----------|--------|
| Template build fails with FAILED status in dashboard | `❌ Build Failed:\n<docker build log>` (last 250 chars shown) | Docker build error — package not found, base image pull failed, or Dockerfile syntax error | foundry_service.py:200-202 |
| Template status stays STAGING | (no dashboard log) | Smelt-Check ran and failed after successful Docker build | foundry_service.py:228-229 |
| Build rejected: unapproved ingredients | HTTP 403: `Build rejected: Blueprint contains unapproved ingredients: [...]` | Smelter is in STRICT mode and blueprint contains packages not in the approved ingredient list | foundry_service.py:59 |
| Build rejected: ingredient not mirrored | HTTP 403: `Build rejected: Ingredient '<pkg>' is approved but not yet mirrored (Status: <status>)` | Package is approved but `mirror_status != MIRRORED` — air-gap mirror not yet populated | foundry_service.py:80-83 |
| `⚠️ environment_service not found at <path>` | `⚠️  environment_service not found at <path> — COPY may fail` | Foundry service cannot locate puppets source directory inside the container | foundry_service.py:170 |

**Smelt-Check Failures** (cluster: RUN-03)

| Symptom | Log line | Root cause | Source |
|---------|----------|-----------|--------|
| Template status FAILED after build succeeded | `❌ Smelt-Check FAILED for <template_name>` | Post-build smoke test (`python --version && pip --version`) failed inside the built image | foundry_service.py:228-229 |
| Template shows amber warning badge | (dashboard badge; no log) | Smelter in WARNING mode found unapproved ingredients — build proceeds but `is_compliant=False` | foundry_service.py:61-62 |

**Registry Issues** (cluster: RUN-03)

| Symptom | Log line | Root cause | Source |
|---------|----------|-----------|--------|
| Template build succeeds but `docker push` fails silently | `PUSH_FAILED: <stderr>` (in ImageResponse status) | Local registry at `localhost:5000` not running, or network route missing | foundry_service.py:308-316 |
| Node cannot pull image from registry at enrollment | (node startup: image pull error) | Registry is running but node container cannot reach `localhost:5000` from within Docker bridge network | MEMORY.md — node networking |

---

## Cross-Link Targets

These are confirmed anchors in existing docs pages that runbooks should reference rather than duplicate:

| Runbook | Scenario | Cross-link |
|---------|----------|-----------|
| nodes.md | Full cert rotation procedure | `../security/mtls.md#certificate-rotation` |
| nodes.md | CRL verification | `../security/mtls.md#certificate-revocation` |
| nodes.md | JOIN_TOKEN generation | `../security/mtls.md#the-join_token` |
| jobs.md | Ed25519 key setup | `../feature-guides/mop-push.md#ed25519-key-setup` |
| jobs.md | Staging review and publish | `../feature-guides/mop-push.md#publish-from-staging` |
| foundry.md | Blueprint format | `../feature-guides/foundry.md#blueprints` |
| foundry.md | Image lifecycle | `../feature-guides/foundry.md#image-lifecycle` |
| foundry.md | Smelter | `../feature-guides/foundry.md#smelter` |
| faq.md | mop-push setup | `../feature-guides/mop-push.md` |
| faq.md | RBAC guide | `../feature-guides/rbac.md` |

**Important:** These anchors are MkDocs-auto-generated from the H2 headers in the target files. They have been verified against the actual header text in committed source. `#certificate-rotation` is the slug of "## Certificate Rotation" in mtls.md.

---

## FAQ Entry Catalogue

Required entries (from CONTEXT.md locked decisions) plus recommended additions drawn from gap reports and MEMORY.md:

### Required Gotchas (4 entries)

1. **Blueprint packages must use `{"python": [...]}` dict format — not a plain list**
   - Root: `foundry_service.py:128` — `packages.get("python", [])` requires a dict with a `"python"` key. A plain list silently results in an empty install.
   - Code: `{"python": ["requests", "numpy"]}` not `["requests", "numpy"]`

2. **`EXECUTION_MODE=direct` required when running Docker-in-Docker**
   - Root: `runtime.py:16-18` — In auto mode, the node tries to spawn Podman/Docker containers. Inside a Docker container (DinD), this hits cgroup v2 issues. `EXECUTION_MODE=direct` runs scripts in the node process instead.
   - Code snippet: `EXECUTION_MODE=direct` in node-compose.yaml environment section.

3. **JOIN_TOKEN is base64-encoded JSON — not a plain API key**
   - Root: `node.py:314-317` — The token is `base64({"t": "<actual_token>", "ca": "<Root_CA_PEM>"})`. Passing a plain string or a truncated/whitespace-polluted token causes `❌ Enrollment Failed`.
   - Tip: Copy the full token exactly from the dashboard's "Generate Join Token" button; even a trailing newline can corrupt it.

4. **`ADMIN_PASSWORD` in `.env` only seeds the admin on first startup**
   - Root: `main.py:84-96` — At startup, if `User(username="admin")` already exists in the DB, the env var is ignored entirely. The DB password is the source of truth for existing deployments.
   - Recovery: Change the password via **Admin → Users → admin → Reset Password** in the dashboard, not by editing `.env`.

### Required How-To Entries (3 entries)

5. **How do I reset a node without re-enrolling?**
   - Answer: You cannot reset a node's identity without re-enrolling. Stop the container, delete `secrets/node-*.crt` and `secrets/node-*.key`, then restart with a fresh JOIN_TOKEN. The orchestrator registers it as a new node. The old node entry (now Offline) can be deleted from the dashboard.
   - Cross-link: `../security/mtls.md#certificate-rotation`

6. **Why does my scheduled job not run at the expected time?**
   - Answer: APScheduler runs in the orchestrator container's timezone (UTC by default). Cron expressions are evaluated in UTC. A job scheduled for `0 9 * * *` fires at 09:00 UTC, not local time.
   - Tip: Use UTC in all cron expressions. Convert local time to UTC before entering the cron field.
   - Cross-link: `../feature-guides/job-scheduling.md`

7. **Can I run jobs without Ed25519 signing?**
   - Answer: No. Signature verification is enforced at the node before any script is executed — it is not configurable. A job submitted without a valid signature is immediately rejected with status `SECURITY_REJECTED`.
   - Cross-link: `../feature-guides/mop-push.md#ed25519-key-setup`

### Recommended Additional Entries (from gap reports and MEMORY.md)

8. **Why does my node appear multiple times in the dashboard?**
   - Root: Duplicate entries happen when `secrets/node-*.crt` was deleted (or the volume was recreated) so the node generated a new UUID and enrolled fresh, while the old entry remained.
   - Recovery: Delete the old Offline entry from the dashboard **Nodes** view. No data is lost.

9. **Why is my Foundry build stuck in STAGING status?**
   - Root: The Smelt-Check smoke test ran and failed after the Docker build succeeded. The template is built but validation failed. Check the orchestrator logs for `❌ Smelt-Check FAILED for <template_name>`.

10. **Why does my node keep getting TAMPERED status?**
    - Root: The zero-trust capability guard detected that the node reported a tool not present in its `expected_capabilities` list. This happens when a tool is installed inside the container after the template was built, or when capability detection changes between restarts.
    - Recovery: Clear the tamper flag via **Nodes → [node] → Clear Tamper** after investigating. If the capability is legitimate, update the expected capabilities via the template rebuild flow.

11. **Why does a job dispatch to a node with insufficient capabilities?**
    - Root: Capability matching requires `node_version >= required_version` using proper semver comparison. If `capability_requirements` is not set on the job, any node is eligible regardless of capabilities.

---

## Code Examples

Verified patterns from source code:

### Node startup log — successful enrollment
```
🚀 Environment Node Started (1)
🔒 Secure Mode Active. Trust Root: /app/secrets/root_ca.crt
[node-abc12345] 📜 Detected Enhanced Token. Bootstrapping Trust...
[node-abc12345] 🔑 Verification Key updated.
[node-abc12345] No identity found. Enrolling with Server...
[node-abc12345] ✅ Enrollment Successful! Certificate Saved.
[node-abc12345] 💓 Heartbeat Thread Started
[node-abc12345] Starting Work Loop...
```
Source: node.py main(), heartbeat_loop(), Node.ensure_identity()

### Node startup log — enrollment failure
```
[node-abc12345] ❌ Enrollment Failed: [Errno 111] Connection refused
```
Source: node.py:420

### Node log — signature verification failure
```
[node-abc12345] ❌ Signature Verification FAILED for Job <guid>: <exception detail>
```
Source: node.py:524

### Node log — verification key missing
```
[node-abc12345] ❌ CRITICAL: Verification Key missing. Cannot verify signature.
```
Source: node.py:511

### Node log — auto runtime detection failure (no container runtime)
```
RuntimeError: No container runtime found and EXECUTION_MODE=auto. Install docker/podman, or set EXECUTION_MODE=direct to opt into running without isolation.
```
Source: runtime.py:30-33

### Foundry log — build failure
```
❌ Build Failed:
<last 250 chars of docker build stdout>
```
Source: foundry_service.py:200-202

### Foundry log — Smelt-Check failure
```
❌ Smelt-Check FAILED for <template_name>
```
Source: foundry_service.py:228

### Foundry log — ingredient not mirrored (HTTP 403 response body)
```
Build rejected: Ingredient '<pkg_name>' is approved but not yet mirrored (Status: <status>). Wait for mirroring to complete or upload the package manually.
```
Source: foundry_service.py:82-83

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Stub `runbooks/index.md` ("coming soon") | Full runbook content across 5 pages | Phase 25 | Operators have actionable recovery steps |
| Gap report as internal reference | Runbook FAQ as operator-facing reference | Phase 25 | Known gotchas are discoverable without reading source code |

**Deprecated/outdated:**
- The `runbooks/index.md` stub content ("Operational runbooks and troubleshooting guides are coming in the next release") is replaced entirely by Phase 25.

---

## Open Questions

1. **Scheduled job timezone — APScheduler default timezone**
   - What we know: APScheduler fires cron jobs in UTC by default. The scheduler_service uses `AsyncIOScheduler()` with no explicit timezone argument.
   - What's unclear: Whether the admin can configure a non-UTC timezone for APScheduler via the Config table.
   - Recommendation: Document the UTC-only behavior and recommend UTC cron expressions. Flag as a potential FAQ entry.

2. **Job timeout — 30-second subprocess limit**
   - What we know: `run_python_script()` in node.py has a 30-second hardcoded timeout. However, the primary execution path for production jobs is `runtime_engine.run()` (no hardcoded timeout).
   - What's unclear: The `run_python_script()` path appears to be an older/fallback path not used in normal job execution. The container runtime path (`runtime.py`) has no timeout set.
   - Recommendation: Document the zombie reaper timeout (configurable via `zombie_timeout_minutes` in Config, default 30 min) as the effective timeout for operators. Do not document the 30-second limit unless it is confirmed to apply to normal job flow.

3. **Registry failure silent push**
   - What we know: `foundry_service.py` does not raise an HTTP error if `docker push` fails — it only logs the failure and returns an ImageResponse with `PUSH_FAILED:` prefix in the status field.
   - What's unclear: Whether the dashboard surfaces the push failure status to the operator or silently shows "Build succeeded."
   - Recommendation: Document the symptom as "Template shows last built time but image is not available on nodes" and instruct operators to check orchestrator logs for `PUSH_FAILED`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend) + vitest (frontend) |
| Config file | `puppeteer/pytest.ini` (or `pyproject.toml`) |
| Quick run command | `cd puppeteer && pytest tests/ -x -q` |
| Full suite command | `cd puppeteer && pytest` |

### Phase Requirements → Test Map

Phase 25 produces MkDocs documentation only — no application code changes. There are no new backend routes, no new frontend components, and no new DB models.

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RUN-01 | nodes.md renders without MkDocs strict errors | smoke | `docker compose -f puppeteer/compose.server.yaml build docs` | ✅ (via Docker build) |
| RUN-02 | jobs.md renders without MkDocs strict errors | smoke | `docker compose -f puppeteer/compose.server.yaml build docs` | ✅ (via Docker build) |
| RUN-03 | foundry.md renders without MkDocs strict errors | smoke | `docker compose -f puppeteer/compose.server.yaml build docs` | ✅ (via Docker build) |
| RUN-04 | faq.md renders without MkDocs strict errors | smoke | `docker compose -f puppeteer/compose.server.yaml build docs` | ✅ (via Docker build) |

**Note:** The only automated validation gate for documentation phases is `mkdocs build --strict` (run inside the Docker builder stage). This catches: broken page references in nav, missing linked pages, and Markdown extension errors. It does not catch broken anchor links. Manual review of anchor targets is required.

### Sampling Rate
- **Per task commit:** Visual review of rendered page in local `mkdocs serve`
- **Per wave merge:** `docker compose -f puppeteer/compose.server.yaml build docs` (strict mode)
- **Phase gate:** Docker build passes before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `docs/docs/runbooks/nodes.md` — stub file required before nav entry is active
- [ ] `docs/docs/runbooks/jobs.md` — stub file required before nav entry is active
- [ ] `docs/docs/runbooks/foundry.md` — stub file required before nav entry is active
- [ ] `docs/docs/runbooks/faq.md` — stub file required before nav entry is active

These stubs (even one-line files) must exist before mkdocs will build without `--strict` warnings from missing nav targets. Wave 0 / Plan 25-01 should create all four stubs plus update the nav in a single task.

---

## Sources

### Primary (HIGH confidence)
- Source code: `puppets/environment_service/node.py` — all node log strings verified verbatim
- Source code: `puppeteer/agent_service/services/foundry_service.py` — all build failure log strings verified verbatim
- Source code: `puppeteer/agent_service/services/job_service.py` — all job status transitions and log strings verified verbatim
- Source code: `puppets/environment_service/runtime.py` — EXECUTION_MODE behavior and RuntimeError message verified verbatim
- `docs/docs/security/mtls.md` — cert rotation procedure and anchor structure confirmed
- `docs/docs/feature-guides/mop-push.md` — signing key setup and anchor structure confirmed
- `docs/docs/feature-guides/foundry.md` — blueprint format and anchor structure confirmed
- `docs/mkdocs.yml` — nav structure and configured extensions confirmed

### Secondary (MEDIUM confidence)
- `puppeteer/agent_service/main.py` (first 100 lines) — admin bootstrap logic confirmed for ADMIN_PASSWORD gotcha
- `.agent/reports/core-pipeline-gaps.md` — historical bug catalogue used to source FAQ gotchas; all resolved bugs used as "known failure modes" for operator guidance

### Tertiary (LOW confidence)
- MEMORY.md — sprint summaries used to confirm which bugs were fixed and which failure modes were real; low confidence as narrative rather than authoritative code

---

## Metadata

**Confidence breakdown:**
- Failure mode catalogue: HIGH — all log strings lifted directly from committed source code
- Cross-link anchors: HIGH — verified against actual H2 headers in target files
- FAQ entries: HIGH (required 4) / MEDIUM (recommended additional 7) — required entries sourced from locked CONTEXT.md decisions backed by code; additional entries from MEMORY.md sprint history
- Validation architecture: HIGH — MkDocs Docker build is the established verification gate from Phases 20–24

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable — no planned changes to log format or error strings)
