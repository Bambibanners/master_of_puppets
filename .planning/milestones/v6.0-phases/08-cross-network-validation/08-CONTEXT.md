# Phase 8: Cross-Network Validation - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Verify that the full mTLS pipeline — enroll, heartbeat, job pull, job execution, and result reporting — works when nodes connect to the puppeteer server across real network interfaces (non-loopback IPs). Validate both Docker and Podman runtimes end-to-end using ephemeral LXC containers. Artifact downloading in this phase means Docker image pull from a cross-network registry; the broader "runtime package repo" feature is out of scope.

</domain>

<decisions>
## Implementation Decisions

### Network topology
- "True cross-network" = LXC containers with separate bridge IPs (non-loopback), all ephemeral via manage-test-nodes (Incus)
- Two full stacks, not just two node LXCs:
  - **Stack 1 (Docker):** LXC 1 = puppeteer server (Docker Compose) + LXC 2 = 2 puppet nodes (Docker job containers)
  - **Stack 2 (Podman):** LXC 3 = puppeteer server (podman-compose) + LXC 4 = 2 puppet nodes (Podman job containers)
- 4 LXCs total, all on the Incus bridge — each gets a distinct IP, no loopback

### Server stack
- Stack 1 server: Docker + Docker Compose, using existing `compose.server.yaml`
- Stack 2 server: podman-compose with `compose.server.yaml` — this is the first validation of Podman server compatibility; gaps should be documented if found
- Each server LXC runs a local Docker/Podman registry for the puppet-node image (not the host's 192.168.50.148:5000)

### Node job execution
- Nodes are never to use `direct` (Python subprocess) mode — always spawn ephemeral child containers
- Stack 1 nodes: `EXECUTION_MODE=docker`, mount Docker socket from LXC host
- Stack 2 nodes: `EXECUTION_MODE=podman`, root Podman inside LXC (cgroupv2 delegation confirmed working in Phase 7 with root — not rootless)
- `EXECUTION_MODE=auto` is acceptable in production; explicit mode set per stack in this test for determinism

### Validation checklist (all must pass for phase complete)
- mTLS enroll + heartbeat: nodes enroll via `install_universal.sh`, receive signed cert, heartbeat appears in `GET /nodes`
- Job dispatch + pull: job dispatched from server, successfully pulled by a node
- Job execution + result: pulled job executes and reports output + exit code back to server
- Multi-node routing: with 4 nodes across 2 LXCs, verify capability/tag-based job targeting assigns job to correct node
- Artifact (image) pull: puppet-node container image pulled from server LXC's local registry across the network
- Node revocation: revoke one node mid-run and confirm it can no longer pull jobs (mTLS cert rejected cross-network)

### Revocation test
- Revoke one of the 4 nodes after enrollment
- Confirm subsequent `/work/pull` calls from that node return 403 (CRL endpoint reachable cross-network)
- Remaining nodes continue to work normally

### Test automation
- New script: `mop_validation/scripts/test_cross_network.py`
- Fully automated end-to-end — no human checkpoints required
- Follows `test_installer_lxc.py` patterns: LXC provisioning, wait-for-heartbeat polling, API-level verification
- Always teardown all 4 LXCs after a run; `--keep` flag preserves them for debugging
- Handles both stacks in one run (sequential: Docker stack first, then Podman stack)

### Claude's Discretion
- Exact Incus provisioning commands for Docker-in-LXC vs Podman-in-LXC
- How to push puppet-node image into each server LXC's local registry
- Test job content (should be simple: a few lines of Python that output a known string)
- Exact polling intervals and timeouts (follow Phase 7 harness patterns)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `mop_validation/scripts/test_installer_lxc.py`: `provision_test_node()`, `wait_for_heartbeat()`, `exec_in_container()` helpers — all reusable patterns for the new script
- `mop_validation/scripts/manage_node.py`: LXC lifecycle management (start/stop); extended for multi-container support if needed
- `puppeteer/installer/install_universal.sh`: fully validated for Ubuntu 24.04 LXC (Phase 7) — use as-is
- `puppeteer/installer/deploy_server.sh`: server-side deployment script from Phase 6 — adapt for LXC server provisioning

### Established Patterns
- `AGENT_URL` must be in both `.env` AND `compose.server.yaml` environment block for Docker Compose to propagate it
- `NODE_IMAGE` env var in compose template allows configurable image reference per deployment
- Server cert SAN automatically includes `AGENT_URL` IP at cert generation time
- `printf '%s'` (not `echo`) for any JSON variables in bash scripts
- `incus exec ... -- bash -c '{json.dumps(cmd)}'` to avoid host-shell evaluation of pipes in test harness
- Rate limit on `POST /admin/generate-token`: ~1 req/30s — get one token per stack and reuse

### Integration Points
- `test_cross_network.py` calls `manage_node.py` (or Incus directly) for LXC lifecycle
- Script must configure `AGENT_URL` and `NODE_IMAGE` on each server LXC to point to LXC-local addresses (not 192.168.50.148)
- Revocation: `DELETE /nodes/{id}` then verify 403 on subsequent `/work/pull` from that node

</code_context>

<specifics>
## Specific Ideas

- Two full stacks (Docker + Podman) is the key structural decision — not just testing nodes in two runtimes, but the entire pipeline including the server
- The Podman server stack (`podman-compose`) is a first-ever validation; any compatibility gaps found should be documented for a future Podman-parity fix phase, not fixed in-situ
- "Artifact downloading" in the phase goal refers to the puppet-node Docker image being pulled from the server LXC's registry across the network — not the script content (which is delivered via the WorkResponse JSON)

</specifics>

<deferred>
## Deferred Ideas

- **Centralized runtime/package repo on puppeteer** — user described a feature where runtimes (Python, Go, etc.), pip packages, and language-specific dependencies are pre-downloaded to the puppeteer and distributed to nodes, with capability flags reflecting what's installed and kept in a local "repo". This is a substantial feature warranting its own milestone, not part of cross-network validation.
- **Podman server compatibility fixes** — if `podman-compose` fails to run `compose.server.yaml` faithfully, document the gaps and defer fixes to a dedicated "Podman parity" phase rather than blocking Phase 8.
- **WAN / internet-grade validation** — testing across separate networks (cloud VM, VPN) is not in scope for Phase 8; LAN LXC bridge is sufficient.

</deferred>

---

*Phase: 08-cross-network-validation*
*Context gathered: 2026-03-07*
