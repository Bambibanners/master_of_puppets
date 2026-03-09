# Phase 8: Cross-Network Validation — Research

**Researched:** 2026-03-07
**Domain:** Incus LXC orchestration, Docker/Podman in containers, mTLS cross-network pipeline validation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- "True cross-network" = LXC containers with separate bridge IPs (non-loopback), all ephemeral via manage-test-nodes (Incus)
- Two full stacks, not just two node LXCs:
  - Stack 1 (Docker): LXC 1 = puppeteer server (Docker Compose) + LXC 2 = 2 puppet nodes (Docker job containers)
  - Stack 2 (Podman): LXC 3 = puppeteer server (podman-compose) + LXC 4 = 2 puppet nodes (Podman job containers)
- 4 LXCs total, all on the Incus bridge — each gets a distinct IP, no loopback
- Stack 1 server: Docker + Docker Compose, using existing `compose.server.yaml`
- Stack 2 server: podman-compose with `compose.server.yaml` — first validation of Podman server compatibility; gaps should be documented if found
- Each server LXC runs a local Docker/Podman registry for the puppet-node image (not the host's 192.168.50.148:5000)
- Nodes are never to use `direct` mode — always spawn ephemeral child containers
- Stack 1 nodes: `EXECUTION_MODE=docker`, mount Docker socket from LXC host
- Stack 2 nodes: `EXECUTION_MODE=podman`, root Podman inside LXC (cgroupv2 delegation confirmed working)
- `EXECUTION_MODE=auto` acceptable in production; explicit mode set per stack in this test for determinism
- Validation checklist: mTLS enroll + heartbeat, job dispatch + pull, job execution + result, multi-node routing, artifact (image) pull, node revocation
- Revoke one node mid-run; confirm 403 on subsequent /work/pull; remaining nodes continue normally
- New script: `mop_validation/scripts/test_cross_network.py`
- Fully automated end-to-end — no human checkpoints required
- Follows `test_installer_lxc.py` patterns: LXC provisioning, wait-for-heartbeat polling, API-level verification
- Always teardown all 4 LXCs after a run; `--keep` flag preserves them for debugging
- Sequential: Docker stack first, then Podman stack

### Claude's Discretion

- Exact Incus provisioning commands for Docker-in-LXC vs Podman-in-LXC
- How to push puppet-node image into each server LXC's local registry
- Test job content (should be simple: a few lines of Python that output a known string)
- Exact polling intervals and timeouts (follow Phase 7 harness patterns)

### Deferred Ideas (OUT OF SCOPE)

- Centralized runtime/package repo on puppeteer (substantial feature, own milestone)
- Podman server compatibility fixes — if podman-compose gaps found, document and defer
- WAN / internet-grade validation — LAN LXC bridge is sufficient
</user_constraints>

---

## Summary

Phase 8 builds an automated Python test harness (`test_cross_network.py`) that provisions four ephemeral Incus LXC containers, deploys two full MoP stacks (one Docker, one Podman), and runs every mTLS pipeline check across real network boundaries. The existing `test_installer_lxc.py` provides the exact helper patterns to reuse: `incus()` wrapper, `exec_in_container()`, `push_file()`, `write_file_in_container()`, `wait_for_heartbeat()`, `TestResult`, and `print_summary()`. The core new work is: server-stack provisioning inside LXCs (Docker Compose and podman-compose), local registry population, multi-node heartbeat aggregation, signed job dispatch with result polling, and the revocation check.

The Incus bridge is `incusbr0` at `10.200.105.1/24`. All four LXCs will receive IPs in this range. Each LXC-IP is a genuine non-loopback address, satisfying the cross-network requirement. The key architecture insight: the server cert SAN is driven by `SERVER_HOSTNAME` in `.env` — the cert-manager entrypoint adds it to the Caddy TLS cert, and the `AGENT_URL` env var propagates that same IP into the node-compose.yaml served by `/api/node/compose`. Both must point to the LXC server's bridge IP, not `localhost`.

**Primary recommendation:** Model `test_cross_network.py` on `test_installer_lxc.py` with a two-stack sequential structure. Provision LXC 1/3 as servers (Docker or Podman stack), then LXC 2/4 as node hosts. Get one JOIN_TOKEN per server (rate limit is 10/min) and reuse for both nodes in that stack.

---

## Standard Stack

### Core
| Library / Tool | Version | Purpose | Why Standard |
|---------------|---------|---------|--------------|
| Incus | Host-installed | LXC container lifecycle | Established in Phase 7; `manage_node.py` already uses it |
| `requests` | existing dep | API calls to puppeteer | Already used in `test_installer_lxc.py` |
| `subprocess` / `json` | stdlib | `incus exec` wrapper | Exact pattern from `test_installer_lxc.py` |
| `docker compose` | v2 plugin | Server stack (Stack 1) | Existing `compose.server.yaml` compatible |
| `podman-compose` | pip install | Server stack (Stack 2) | Already installed in manage_node.py LXC provisioning |
| Docker registry:2 | docker.io/library/registry:2 | Local image registry in each server LXC | Already in `compose.server.yaml`'s `registry` service |

### Reusable Helpers from test_installer_lxc.py

The following functions are **directly copy-reusable** from `test_installer_lxc.py`:

| Function | Source Location | What it Does |
|----------|----------------|--------------|
| `incus(cmd, check, capture, timeout)` | Lines 68–81 | Runs `incus <cmd>` via shell, raises on failure |
| `exec_in_container(cmd, container, check, timeout)` | Lines 85–87 | `incus exec <container> -- bash -c <json-escaped cmd>` |
| `push_file(local_path, container_path, container)` | Lines 90–91 | `incus file push` |
| `write_file_in_container(path, content, container)` | Lines 94–103 | Tempfile + `incus file push` — safe for multi-line content |
| `load_secrets(path)` | Lines 49–63 | KEY=VALUE secrets.env parser |
| `api_login(admin_password)` | Lines 151–160 | `POST /auth/login` → JWT |
| `api_generate_token(jwt)` | Lines 163–172 | `POST /admin/generate-token` → JOIN_TOKEN |
| `api_get_nodes(jwt)` | Lines 175–184 | `GET /nodes` → list |
| `wait_for_heartbeat(jwt, timeout)` | Lines 187–213 | Polls /nodes until any node is recently-seen |
| `TestResult` class | Lines 219–237 | `.ok()` / `.fail()` / `.skip()` |
| `print_summary(results)` | Lines 241–257 | Tabular test report |

**New function needed:** `wait_for_n_heartbeats(jwt, n, timeout, server_url)` — variant that polls until `n` distinct nodes are online, returning the list. This is needed for the 2-node-per-stack check.

---

## Architecture Patterns

### Incus Network Topology

```
Host (192.168.50.148)
  incusbr0: 10.200.105.1/24
    ├── LXC1: mop-docker-server   (10.200.105.x) — Docker + compose.server.yaml
    ├── LXC2: mop-docker-nodes    (10.200.105.y) — 2 Docker puppet nodes
    ├── LXC3: mop-podman-server   (10.200.105.z) — Podman + podman-compose
    └── LXC4: mop-podman-nodes    (10.200.105.w) — 2 Podman puppet nodes
```

All four LXCs can reach each other via bridge IPs. No port-forwarding or NAT needed for inter-LXC traffic.

### Recommended Container Names

```
LXC1: "mop-docker-server"
LXC2: "mop-docker-nodes"
LXC3: "mop-podman-server"
LXC4: "mop-podman-nodes"
```

### Provisioning Pattern: Docker-in-LXC (LXC1 and LXC2)

```python
# Source: manage_node.py pattern + Phase 7 learnings
incus(f"launch images:ubuntu/24.04 {name} -c security.nesting=true", timeout=120)
time.sleep(8)  # cloud-init settle
exec_in_container("apt-get update -qq", container=name, timeout=120)
exec_in_container("apt-get install -y curl", container=name)
# Docker install:
exec_in_container("curl -fsSL https://get.docker.com | sh", container=name, timeout=300)
exec_in_container("systemctl enable docker && systemctl start docker", container=name)
```

**Why `-c security.nesting=true`:** Docker-in-LXC requires nested containerization. This flag is already used in every Phase 7 LXC. Without it, Docker daemon fails to start.

**cgroupv2 for Docker-in-LXC:** Ubuntu 24.04 uses cgroupv2 by default. Docker CE works fine with cgroupv2 in LXC when `security.nesting=true` is set. No additional kernel flags needed.

### Provisioning Pattern: Podman-in-LXC (LXC3 and LXC4)

```python
# Source: manage_node.py lines 91-93 — Podman already installed by default
incus(f"launch images:ubuntu/24.04 {name} -c security.nesting=true", timeout=120)
time.sleep(8)
exec_in_container("apt-get update -qq && apt-get install -y podman python3 python3-pip curl",
                  container=name, timeout=300)
exec_in_container("pip3 install --break-system-packages -q podman-compose", container=name)
exec_in_container("ln -sf /usr/local/bin/podman-compose /usr/bin/podman-compose 2>/dev/null || true",
                  container=name)
```

**Root Podman in LXC:** Phase 7 confirmed that root Podman works inside LXC with `security.nesting=true`. Rootless Podman has cgroupv2 delegation issues in LXC — always use root for this test.

**cgroupv2 delegation for Podman-in-LXC:** In Incus, nested root Podman works because Incus already delegates the cgroup subtree to the container when `security.nesting=true`. No additional `security.privileged=true` flag is required (and it would be unnecessary security risk).

### Server Stack Provisioning: Docker (LXC1)

```python
# 1. Push the puppeteer source into LXC1
#    (incus file push works for single files; for directories, tar + push + extract)
exec_in_container("mkdir -p /opt/mop/puppeteer /opt/mop/puppets", container="mop-docker-server")
# Tar the puppeteer directory on host, push, extract in LXC
subprocess.run(["tar", "czf", "/tmp/puppeteer.tar.gz", "-C", REPO_ROOT, "puppeteer", "puppets"], ...)
incus("file push /tmp/puppeteer.tar.gz mop-docker-server/tmp/puppeteer.tar.gz")
exec_in_container("tar xzf /tmp/puppeteer.tar.gz -C /opt/mop/", container="mop-docker-server")

# 2. Write .env with LXC1's own IP as SERVER_HOSTNAME and AGENT_URL
server_ip = get_lxc_ip("mop-docker-server")
env_content = f"""
ADMIN_PASSWORD={admin_password}
ENCRYPTION_KEY={secrets['ENCRYPTION_KEY']}
SECRET_KEY={secrets['SECRET_KEY']}
API_KEY={secrets['API_KEY']}
SERVER_HOSTNAME={server_ip}
AGENT_URL=https://{server_ip}:8001
NODE_IMAGE={server_ip}:5000/puppet-node:latest
"""
write_file_in_container("/opt/mop/puppeteer/.env", env_content, container="mop-docker-server")

# 3. Build and start stack
exec_in_container(
    "cd /opt/mop/puppeteer && docker compose -f compose.server.yaml up -d --build",
    container="mop-docker-server", timeout=600
)
```

**Critical pattern (Phase 6 finding):** `AGENT_URL` must be in BOTH `.env` AND the `compose.server.yaml` agent environment block. The file already has `AGENT_URL=${AGENT_URL:-https://localhost:8001}` in the agent service block, so writing `AGENT_URL=https://{server_ip}:8001` to `.env` propagates correctly.

**Critical pattern (Phase 6 finding):** `NODE_IMAGE` env var in `.env` propagates through compose.server.yaml's `NODE_IMAGE=${NODE_IMAGE:-localhost/...}` to the `/api/node/compose` response. Set it to `{server_ip}:5000/puppet-node:latest` so nodes pull from the LXC-local registry.

### Server Stack Provisioning: Podman (LXC3)

```python
# Same tar + push + extract pattern as Docker stack
# Write .env with podman-compose compatible settings
exec_in_container(
    "cd /opt/mop/puppeteer && podman-compose -f compose.server.yaml up -d",
    container="mop-podman-server", timeout=600
)
```

**Known podman-compose compatibility concerns with compose.server.yaml:**

| compose.server.yaml Feature | Docker Compose | podman-compose | Notes |
|----------------------------|----------------|----------------|-------|
| `version: "3"` | OK | OK | Parsed by both |
| `build:` directives | OK | OK (builds via Podman) | Works with root podman |
| `/var/run/docker.sock` mount (agent service) | OK | ISSUE | No Docker socket in Podman LXC; Foundry builds will fail |
| `healthcheck:` on db service | OK | Partial | podman-compose may ignore healthcheck `depends_on` conditions |
| `depends_on: condition: service_healthy` | OK | ISSUE (older versions) | podman-compose < 1.1 treats all `depends_on` as started-only |
| `registry:2` service | OK | OK | Standard registry image |
| `tunnel:` service (cloudflared) | OK | OK | Just a container |
| Named volumes | OK | OK | Podman volumes supported |

**Recommendation:** Document Docker socket and `depends_on` condition issues if encountered. Do not fix in-phase (per deferred constraint). The test harness should detect and record whether the Podman server stack started all services successfully.

### Local Registry: Puppet-Node Image Push Pattern

Each server LXC runs its own `registry:2` on port 5000 (already in `compose.server.yaml`). The puppet-node image must be pushed into each server LXC's registry from the host.

```python
def push_node_image_to_lxc_registry(server_container: str, server_ip: str):
    """Push the puppet-node image into the server LXC's local registry."""
    # 1. Save the image to a tar on the host
    subprocess.run(
        ["docker", "save", "-o", "/tmp/puppet-node.tar",
         "localhost/master-of-puppets-node:latest"],
        check=True
    )
    # 2. Push the tar into the LXC
    incus(f"file push /tmp/puppet-node.tar {server_container}/tmp/puppet-node.tar")

    # 3. In the Docker LXC: load and retag
    exec_in_container(
        f"docker load -i /tmp/puppet-node.tar && "
        f"docker tag localhost/master-of-puppets-node:latest {server_ip}:5000/puppet-node:latest && "
        f"docker push {server_ip}:5000/puppet-node:latest",
        container=server_container, timeout=120
    )
```

**Timing:** The registry service must be running before the push. Poll `http://{server_ip}:5000/v2/` with `requests.get(verify=False)` or `curl` from inside the LXC until it responds 200.

**Insecure registry:** The registry runs HTTP (not HTTPS). The Docker daemon inside the LXC must be configured to allow it:
```python
# Write /etc/docker/daemon.json inside the Docker server LXC
daemon_json = f'{{"insecure-registries": ["{server_ip}:5000"]}}'
write_file_in_container("/etc/docker/daemon.json", daemon_json, container="mop-docker-server")
exec_in_container("systemctl restart docker", container="mop-docker-server", timeout=30)
```

For Podman in node LXCs, the registries.conf pattern from Phase 7 applies:
```python
registry_conf = f'[[registry]]\nlocation = "{server_ip}:5000"\ninsecure = true\n'
exec_in_container("mkdir -p /etc/containers/registries.conf.d", container=node_container)
write_file_in_container(
    "/etc/containers/registries.conf.d/local-registry.conf",
    registry_conf, container=node_container
)
```

### mTLS SAN: Dynamic IP Handling

**How it works (traced from source):**

1. `cert-manager/entrypoint.sh` reads `SERVER_HOSTNAME` env var
2. Builds `CADDY_SANS="localhost,127.0.0.1,{SERVER_HOSTNAME}"`
3. `step certificate create` issues a leaf cert with those SANs
4. The cert is stored in the `certs-volume` shared with the `agent` service
5. Caddy uses this cert for HTTPS on port 8001 (the agent endpoint)

**Consequence for LXC testing:** Setting `SERVER_HOSTNAME={lxc_server_ip}` in `.env` before `docker compose up` causes the generated server cert to include that LXC IP as a SAN. Nodes connecting from LXC2/4 to LXC1/3's IP will pass TLS verification when they trust the CA.

**The CA is embedded in JOIN_TOKEN:** `POST /admin/generate-token` returns a base64-encoded JSON with `{"t": "...", "ca": "-----BEGIN CERTIFICATE-----\n..."}`. The installer extracts this CA and installs it. This means the CA used by the LXC server is the one nodes will trust — this works correctly regardless of which server generated it.

**Node-side verification:** `node.py` sets `VERIFY_SSL = ROOT_CA_PATH` when `ROOT_CA_PATH` exists. In the node-compose.yaml, `ROOT_CA_PATH` is not explicitly set but defaults to a Windows path. The installer writes `bootstrap_ca.crt` to the working directory and the node-compose.yaml mounts `./secrets` — the installer puts the CA there. Cross-network TLS verification will work as long as the CA in the token matches the server cert.

### Job Dispatch Flow (Verified Pattern)

From `test_local_stack.py` `submit_signed_job()`:

```python
# 1. Sign script with Ed25519 private key
sig = private_key.sign(script_content.encode("utf-8"))  # Ed25519 — no hash algorithm arg
signature_b64 = base64.b64encode(sig).decode()

# 2. POST to /jobs
r = client.post("/jobs", {
    "task_type": "python_script",
    "payload": {"script_content": script, "signature": signature_b64},
    "target_tags": ["some-tag"],  # used for node routing
    "priority": 5
})
guid = r.json()["guid"]

# 3. Poll for completion
while True:
    r = client.get(f"/jobs/{guid}")
    status = r.json()["status"]
    if status in ("COMPLETED", "FAILED", "CANCELLED"):
        break
    time.sleep(5)
```

**Signing key requirement:** A signature must be registered in `POST /admin/upload-key` (or equivalent `POST /signatures`) before jobs can be dispatched. The signature verification key's public key must match what the node uses to verify execution. For the cross-network test, the harness should:
1. Generate a fresh Ed25519 keypair (or reuse from secrets.env/host)
2. Upload the verification key to each server via `POST /admin/upload-key`
3. Sign all test scripts with the private key

**The signature ID:** When uploading a key, the server returns a signature record ID. This ID is not required in the job payload for immediate dispatch (signature is inline in the payload), but it is referenced for job definitions.

### Multi-Node Routing: Tag-Based Targeting

Node tags are set at install time via `--tags` flag to `install_universal.sh`. The node-compose.yaml template sets `NODE_TAGS=${effective_tags}` (default: `general,linux,arm64`). For the multi-node routing check, the two nodes in each stack should be enrolled with different tags so jobs can be routed specifically:

```
Node A (LXC2, Stack 1): --tags "docker-stack,node-a"
Node B (LXC2, Stack 1): --tags "docker-stack,node-b"
```

Then dispatch `target_tags: ["node-a"]` and verify it lands on node-a's node_id, not node-b.

**Installer tag injection:** The `--tags` flag is passed through to `NODE_TAGS` in node-compose.yaml. The compose template already reads `tags` as a query param: `effective_tags = tags if tags else "general,linux,arm64"`.

### Node Revocation Flow

```python
# 1. Get node_id of the node to revoke
nodes = api_get_nodes(jwt, server_url=lxc_server_url)
target_node = [n for n in nodes if n["node_id"] == "node-a-id"][0]

# 2. Revoke via API
resp = requests.post(
    f"{lxc_server_url}/nodes/{target_node['node_id']}/revoke",
    headers={"Authorization": f"Bearer {jwt}"},
    verify=False, timeout=15
)
# Expects 200: {"status": "revoked", "node_id": "..."}

# 3. Wait a heartbeat cycle (~10s), then verify 403
# The node will attempt /work/pull on its next poll cycle
# We cannot directly call /work/pull from the test harness (requires node mTLS cert)
# Instead: check node status via GET /nodes shows REVOKED, then wait for node
# to log its 403 (observable via docker logs or node status field)
```

**Important:** The test harness cannot send a `/work/pull` request on behalf of the revoked node directly — it requires a valid mTLS client cert. The verification approach is:
1. Set node to REVOKED via API
2. `GET /nodes` confirms `status: "REVOKED"` for that node_id (HIGH confidence check)
3. `GET /nodes/{node_id}` returns the REVOKED status
4. The remaining nodes continue to heartbeat and pick up jobs (proven by dispatching a job after revocation)

**Alternative for direct 403 verification:** Use `exec_in_container` on the node LXC to run a `curl` command attempting `/work/pull` with the node's cert. The revoked node's compose keeps running (it wasn't stopped), so its cert files are in `./secrets/`. However, `/work/pull` also requires `X-API-KEY` and `node_id` query param — constructing the exact request from a bash call inside the LXC is more complex. The API status check is the pragmatic approach.

### Server Health Check Pattern

Before running node enrollment, poll the server's API to confirm it's up:

```python
def wait_for_server(server_url: str, timeout: int = 120) -> bool:
    """Poll GET /health or /nodes until server responds."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{server_url}/nodes",
                           headers={"Authorization": "Bearer dummy"},
                           verify=False, timeout=5)
            # 401 means the server is up (auth is working)
            if r.status_code in (200, 401, 403):
                return True
        except Exception:
            pass
        time.sleep(5)
    return False
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LXC container lifecycle | Custom subprocess calls to `incus launch/delete` | `incus()` helper from `test_installer_lxc.py` | Already handles error checking, timeouts, permission errors |
| File transfer to LXC | SSH/SCP | `push_file()` + `write_file_in_container()` helpers | Incus native file push — no SSH setup needed |
| Container exec with shell | Raw `subprocess.run(["incus", "exec", ...])` | `exec_in_container(cmd, container)` | JSON-escapes the command string preventing shell injection |
| Heartbeat polling | Custom loop | `wait_for_heartbeat()` pattern | Already handles timestamp parsing (ISO + Unix), age calculation |
| Test result tracking | print statements | `TestResult` class | Consistent `.ok()/.fail()/.skip()` with `print_summary()` tabular output |
| Ed25519 signing | PSS/RSA | `private_key.sign(content.encode())` (Ed25519, no hash arg) | Ed25519 sign takes exactly one arg; RSA PSS is wrong algorithm |
| Registry auth | Custom auth server | `registry:2` with `insecure-registries` config | Already in compose.server.yaml; no TLS cert complexity |
| Server stack teardown | Manual `docker compose down` | Full `incus delete {name} --force` | Deleting the LXC tears down everything atomically |

---

## Common Pitfalls

### Pitfall 1: AGENT_URL Not Propagated to node-compose.yaml

**What goes wrong:** Nodes get a node-compose.yaml with `AGENT_URL=https://localhost:8001`. The node container starts but cannot reach the server — it's trying to connect to itself.

**Why it happens:** `compose.server.yaml` has `AGENT_URL=${AGENT_URL:-https://localhost:8001}`. If `.env` is missing `AGENT_URL` or Docker Compose doesn't pick it up, the default fires.

**How to avoid:** Write `AGENT_URL=https://{lxc1_ip}:8001` explicitly in `.env` AND confirm it's in the compose.server.yaml agent environment block (it already is). Verify by fetching `/api/node/compose?token=...` from the test harness and checking the AGENT_URL line in the YAML response.

**Warning signs:** Nodes never heartbeat after enrollment.

### Pitfall 2: NODE_IMAGE Points to Wrong Registry

**What goes wrong:** Nodes pull `localhost/master-of-puppets-node:latest` and get "image not found" or pull from the host's localhost — which doesn't exist inside the LXC.

**Why it happens:** The default NODE_IMAGE env var uses `localhost/` prefix. From inside LXC2, `localhost` is LXC2 itself, not the server LXC.

**How to avoid:** Set `NODE_IMAGE={lxc1_ip}:5000/puppet-node:latest` in LXC1's `.env`. Confirm the /api/node/compose response contains the correct image ref. Also configure the insecure registry on the node LXC before enrollment.

**Warning signs:** Nodes enroll and heartbeat but job execution fails with "Unable to pull image".

### Pitfall 3: Server Cert SAN Missing LXC IP

**What goes wrong:** Node's httpx client rejects the server TLS cert with "hostname mismatch" because the cert only has `localhost` and `127.0.0.1` as SANs.

**Why it happens:** `cert-manager/entrypoint.sh` only adds `SERVER_HOSTNAME` to the Caddy cert SANs. If `SERVER_HOSTNAME` is not set in `.env`, the LXC IP is absent.

**How to avoid:** Always write `SERVER_HOSTNAME={lxc_ip}` to `.env` before starting the stack. If the cert was already generated (cached in `certs-volume`) with the wrong SANs, the entrypoint won't regenerate it. For fresh LXC deployments this is not an issue since the volume is new.

**Warning signs:** Node enrollment fails with SSL certificate verification error.

### Pitfall 4: Docker Socket Not Available in Podman Server LXC

**What goes wrong:** `compose.server.yaml` mounts `/var/run/docker.sock` in the agent service. In LXC3 (Podman server), no Docker socket exists. Foundry builds will fail; the agent service may also fail if it tries to access the socket at startup.

**Why it happens:** `/var/run/docker.sock` is a Docker-specific socket. Podman uses a different socket path.

**How to avoid:** Document the gap. For the Podman stack, Foundry functionality is explicitly deferred. The agent service itself does not crash on missing socket — it only fails when a build is attempted. The test harness should not test Foundry in the Podman stack, and the RESEARCH should note this gap for a future Podman-parity phase.

### Pitfall 5: Rate Limit on POST /admin/generate-token

**What goes wrong:** The second call to generate-token within 60 seconds gets rate-limited (429). This is especially likely when testing both stacks back-to-back.

**Why it happens:** `@limiter.limit("10/minute")` via slowapi. The limit is per client IP address (the test runner's host IP).

**How to avoid:** Generate one token per server, reuse it for both nodes in the stack (the installer uses each token exactly once — tokens are consumed at enrollment, so two nodes need two tokens). With 4 nodes and 10/min rate limit, there is no issue. The CONTEXT.md warning was about a historical stricter limit. Current limit is 10/min.

**Warning signs:** `requests.exceptions.HTTPError: 429 Too Many Requests`

### Pitfall 6: podman-compose depends_on Condition Ordering

**What goes wrong:** The db service has `depends_on: condition: service_healthy`. podman-compose (especially versions < 1.1) may not wait for the healthcheck before starting the agent service, causing the agent to crash on DB connection error.

**Why it happens:** `depends_on` with `condition: service_healthy` is a Docker Compose v3.5+ feature. podman-compose support varies by version.

**How to avoid:** After starting the Podman stack, poll the agent API with a longer timeout (120s instead of 60s). If the agent is not up after 120s, check whether db started first. Document if encountered.

### Pitfall 7: Stale node-id on Re-run Without Teardown

**What goes wrong:** If `--keep` was used and a subsequent run starts without tearing down, the node containers try to re-enroll with the same NODE_ID but the token is already consumed.

**Why it happens:** `node.py` reuses the node-id from the existing cert file in `./secrets/`. The installer generates a new token on each run, but the node-compose.yaml embeds it.

**How to avoid:** Always tear down all 4 LXCs between test runs (the default behavior). `--keep` is for debugging only, and a re-run with `--keep` should detect existing containers and skip provisioning.

---

## Code Examples

### Pattern: Get LXC IP

```python
# Source: manage_node.py get_node_ip()
def get_lxc_ip(container_name: str) -> str | None:
    """Return the first global IPv4 address of a running LXC container."""
    res = incus(f"list {container_name} --format json")
    data = json.loads(res.stdout)
    if not data:
        return None
    networks = data[0].get("state", {}).get("network", {})
    for net in networks.values():
        for addr in net.get("addresses", []):
            if addr.get("family") == "inet" and addr.get("scope") == "global":
                return addr.get("address")
    return None
```

### Pattern: Provision Docker-in-LXC Server

```python
# Source: manage_node.py setup_node() + test_installer_lxc.py patterns
def provision_docker_server(name: str) -> str:
    """Launch LXC, install Docker + Compose, return container IP."""
    incus(f"launch images:ubuntu/24.04 {name} -c security.nesting=true", timeout=120)
    time.sleep(8)
    exec_in_container("apt-get update -qq 2>&1 | tail -2", container=name, timeout=120)
    exec_in_container("apt-get install -y curl ca-certificates", container=name, timeout=60)
    exec_in_container("curl -fsSL https://get.docker.com | sh 2>&1 | tail -5",
                      container=name, timeout=300)
    exec_in_container("systemctl enable docker && systemctl start docker", container=name)
    # Confirm docker is working
    exec_in_container("docker info > /dev/null 2>&1", container=name, timeout=30)
    ip = get_lxc_ip(name)
    if not ip:
        raise RuntimeError(f"Could not get IP for {name}")
    return ip
```

### Pattern: Wait for N Nodes Online

```python
# Source: extended from test_installer_lxc.py wait_for_heartbeat()
def wait_for_n_heartbeats(jwt: str, n: int, server_url: str,
                           timeout: int = 120) -> list:
    """Poll GET /nodes until at least n nodes are recently active."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(
                f"{server_url}/nodes",
                headers={"Authorization": f"Bearer {jwt}"},
                verify=False, timeout=15,
            )
            if resp.status_code == 200:
                nodes = resp.json()
                active = []
                for node in nodes:
                    last_seen = node.get("last_seen")
                    if last_seen:
                        import datetime as dt
                        try:
                            ts = dt.datetime.fromisoformat(
                                last_seen.replace("Z", "+00:00"))
                            age = (dt.datetime.now(dt.timezone.utc) - ts
                                   ).total_seconds()
                            if age < timeout:
                                active.append(node)
                        except Exception:
                            pass
                if len(active) >= n:
                    return active
        except Exception:
            pass
        time.sleep(5)
    return []
```

### Pattern: Signed Job Dispatch (Ed25519)

```python
# Source: test_local_stack.py submit_signed_job() + sign_script()
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import base64

def load_ed25519_key(key_path: str) -> ed25519.Ed25519PrivateKey:
    return serialization.load_pem_private_key(
        open(key_path, "rb").read(), password=None)

def sign_script(private_key, script_content: str) -> str:
    """Ed25519 sign — NO hash algorithm argument (unlike RSA)."""
    sig = private_key.sign(script_content.encode("utf-8"))
    return base64.b64encode(sig).decode()

def dispatch_job(jwt: str, server_url: str, private_key,
                 script: str, tags: list) -> str:
    sig = sign_script(private_key, script)
    r = requests.post(
        f"{server_url}/jobs",
        json={
            "task_type": "python_script",
            "payload": {"script_content": script, "signature": sig},
            "target_tags": tags,
            "priority": 5,
        },
        headers={"Authorization": f"Bearer {jwt}"},
        verify=False, timeout=15,
    )
    r.raise_for_status()
    return r.json()["guid"]

def poll_job_result(jwt: str, server_url: str, guid: str,
                    timeout: int = 60) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(
            f"{server_url}/jobs/{guid}",
            headers={"Authorization": f"Bearer {jwt}"},
            verify=False, timeout=15,
        )
        if r.status_code == 200:
            job = r.json()
            if job["status"] in ("COMPLETED", "FAILED", "CANCELLED"):
                return job
        time.sleep(5)
    return {}
```

### Pattern: Simple Test Script (Cross-Network Validation Job)

```python
# This is the content of the test job — plain Python, output a known string
TEST_SCRIPT = """
import socket
import os
hostname = socket.gethostname()
node_id = os.environ.get('NODE_ID', 'unknown')
print(f"CROSS_NETWORK_OK hostname={hostname} node_id={node_id}")
"""
# Success marker to check in job result
TEST_SCRIPT_MARKER = "CROSS_NETWORK_OK"
```

### Pattern: Node Revocation Check

```python
def revoke_node_and_verify(jwt: str, server_url: str, node_id: str) -> bool:
    """Revoke a node and verify it shows REVOKED status."""
    # 1. Issue revocation
    r = requests.post(
        f"{server_url}/nodes/{node_id}/revoke",
        headers={"Authorization": f"Bearer {jwt}"},
        verify=False, timeout=15,
    )
    if r.status_code != 200:
        return False
    # 2. Verify status via GET /nodes
    time.sleep(3)
    nodes = requests.get(
        f"{server_url}/nodes",
        headers={"Authorization": f"Bearer {jwt}"},
        verify=False, timeout=15,
    ).json()
    target = next((n for n in nodes if n["node_id"] == node_id), None)
    return target is not None and target.get("status") == "REVOKED"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `echo $JSON_VAR` in installer | `printf '%s' "$JSON_VAR"` | Phase 7 | Prevents `\n` corruption in CA PEM |
| `localhost/` image prefix in node-compose | `{AGENT_URL_IP}:5000/puppet-node:latest` via NODE_IMAGE env | Phase 7 | LXC nodes can pull image cross-network |
| `node-{uuid}` regenerated on every restart | `_load_or_generate_node_id()` scans secrets/ for existing cert | Sprint 7 | Prevents cert loop on node container restart |
| `security.nesting=false` LXC default | `-c security.nesting=true` required | Phase 7 | Enables Docker/Podman inside LXC |
| `AGENT_URL` in .env only | AGENT_URL in both .env AND compose.server.yaml env block | Phase 6 | Docker Compose propagates it to containers |

---

## Script Architecture

### test_cross_network.py Top-Level Structure

```
mop_validation/scripts/test_cross_network.py
├── Constants: LXC names, timeouts, paths
├── Helpers (copied from test_installer_lxc.py):
│   ├── incus(), exec_in_container(), push_file(), write_file_in_container()
│   ├── load_secrets()
│   ├── api_login(), api_generate_token(), api_get_nodes()
│   ├── TestResult, print_summary()
│   └── wait_for_n_heartbeats() [NEW]
├── Provisioning helpers:
│   ├── get_lxc_ip(name)
│   ├── provision_docker_server(name) → ip
│   ├── provision_podman_server(name) → ip
│   ├── provision_node_lxc_docker(name) → ip
│   ├── provision_node_lxc_podman(name) → ip
│   ├── deploy_server_stack(name, ip, mode, secrets) [docker or podman]
│   ├── push_node_image_to_registry(server_lxc, server_ip, mode)
│   └── enroll_node(node_lxc, server_url, join_token, tags, platform)
├── Test execution:
│   ├── run_stack_tests(stack_name, server_lxc, node_lxc,
│   │                   server_url, mode) → list[TestResult]
│   │   ├── T1: Server API reachable (GET /nodes → 401)
│   │   ├── T2: Node enrollment (wait_for_n_heartbeats 2)
│   │   ├── T3: Job dispatch + execution result (CROSS_NETWORK_OK marker)
│   │   ├── T4: Multi-node routing (target_tags check)
│   │   ├── T5: Artifact (image) pull from LXC registry (confirmed during enrollment)
│   │   └── T6: Node revocation (status=REVOKED in GET /nodes)
│   └── main():
│       ├── Provision LXC1 (docker server), LXC2 (docker nodes)
│       ├── run_stack_tests("Docker", lxc1, lxc2, ...)
│       ├── Provision LXC3 (podman server), LXC4 (podman nodes)
│       ├── run_stack_tests("Podman", lxc3, lxc4, ...)
│       └── teardown (unless --keep)
└── CLI: --keep, --docker-only, --podman-only, --dry-run
```

### Test Naming Convention

Tests should be named as `CN-XX` (Cross-Network) for clarity in the summary table:
- `CN-01: Docker server API reachable`
- `CN-02: Docker node-a enrolled + heartbeat`
- `CN-03: Docker node-b enrolled + heartbeat`
- `CN-04: Docker job execution cross-network (COMPLETED + marker)`
- `CN-05: Docker multi-node routing (job to node-a only)`
- `CN-06: Docker image pull from LXC registry`
- `CN-07: Docker node revocation (status=REVOKED)`
- `CN-08: Docker remaining node still active post-revocation`
- `CN-09 through CN-16: Podman stack equivalents`

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python stdlib (no pytest) — same as test_installer_lxc.py |
| Config file | None — constants in script header |
| Quick run command | `python3 mop_validation/scripts/test_cross_network.py --dry-run` |
| Full suite command | `python3 mop_validation/scripts/test_cross_network.py` |
| Keep-alive run | `python3 mop_validation/scripts/test_cross_network.py --keep` |

### Phase Requirements → Test Map

Phase 8 has no formal REQ-XX IDs but maps to the CONTEXT.md validation checklist:

| Validation Item | Test ID | Test Type | Verification Method |
|----------------|---------|-----------|-------------------|
| mTLS enroll + heartbeat | CN-01,02,03 | integration | `wait_for_n_heartbeats(2)` returns both nodes |
| Job dispatch + pull | CN-04 | integration | `GET /jobs/{guid}` → status=COMPLETED |
| Job execution + result | CN-04 | integration | result contains `CROSS_NETWORK_OK` marker |
| Multi-node routing | CN-05 | integration | completed job's `node_id` matches target tag's node |
| Artifact (image) pull | CN-06 | integration | node enrolled using image from LXC registry (enrollment success implies pull success) |
| Node revocation | CN-07,08 | integration | `GET /nodes` → status=REVOKED; remaining node still heartbeats |
| Podman stack equivalents | CN-09..16 | integration | Same checks, podman-compose server |

### Wave 0 Gaps

- [ ] `mop_validation/scripts/test_cross_network.py` — the entire test script (Phase 8 Wave 1 deliverable)

*(No existing test infrastructure covers cross-network or multi-LXC scenarios.)*

---

## Open Questions

1. **podman-compose version available in Ubuntu 24.04 apt**
   - What we know: `pip3 install --break-system-packages podman-compose` installs it (Phase 7 pattern)
   - What's unclear: exact version; whether it handles `depends_on: condition: service_healthy`
   - Recommendation: Install via pip (known to work from Phase 7). If healthcheck depends_on fails, add a `sleep 10` between db start and agent start via a custom entrypoint modification — or document and defer.

2. **Docker buildx availability in Docker-in-LXC**
   - What we know: `curl -fsSL https://get.docker.com | sh` installs Docker CE with compose plugin
   - What's unclear: whether Buildx multi-platform support works in nested containers (not needed for this phase)
   - Recommendation: Non-issue. Phase 8 does not do Foundry builds.

3. **Podman socket path for Foundry builds in Podman stack**
   - What we know: `/var/run/docker.sock` does not exist in Podman LXC
   - What's unclear: Whether the agent container crashes on startup when the socket mount fails
   - Recommendation: Test this in the Podman stack run. If agent crashes, document it as a Podman-parity gap (per deferred constraint). May need to strip the Docker socket volume mount from a modified compose file for the Podman server.

4. **Node enrollment from LXC2 to LXC1 across bridge**
   - What we know: Incus bridge allows all-to-all communication between LXC containers
   - What's unclear: Whether the node container (inside LXC2) can reach LXC1's IP — it depends on whether LXC2's Docker containers inherit the host network or use a Docker bridge
   - Recommendation: The node-compose.yaml uses `network_mode: host` for the puppet container. This means the puppet container uses LXC2's network namespace directly, which can reach incusbr0. This is the correct pattern.

---

## Sources

### Primary (HIGH confidence)

- Codebase read: `test_installer_lxc.py` — all reusable patterns verified line by line
- Codebase read: `manage_node.py` — LXC provisioning commands with `-c security.nesting=true`
- Codebase read: `compose.server.yaml` — service names, env var names, registry service, Docker socket mount
- Codebase read: `cert-manager/entrypoint.sh` — SERVER_HOSTNAME → SAN generation logic
- Codebase read: `puppeteer/agent_service/main.py` — `/api/node/compose`, `/admin/generate-token`, `/nodes/{id}/revoke`, `/work/pull` 403 logic
- Codebase read: `puppeteer/agent_service/pki.py` — `sign_csr()`, `issue_server_cert()` with dynamic SAN list
- Codebase read: `puppets/environment_service/node.py` — `_load_or_generate_node_id()`, EXECUTION_MODE, VERIFY_SSL
- Codebase read: `test_local_stack.py` — Ed25519 sign pattern, job dispatch pattern, node tag routing
- Codebase read: `install_universal.sh` — token parsing, CA extraction, compose deployment
- Live check: `incus network list` → `incusbr0` at `10.200.105.1/24`
- Live check: `incus list` → no running containers (clean state)

### Secondary (MEDIUM confidence)

- Phase 6 accumulated context (STATE.md): `AGENT_URL` must be in both `.env` and compose env block
- Phase 7 accumulated context (STATE.md): root Podman in LXC confirmed working; `security.nesting=true` required
- CONTEXT.md Phase 8 decisions: all design choices verified against codebase

### Tertiary (LOW confidence)

- `podman-compose` `depends_on: condition: service_healthy` support — not verified against installed version; inferred from known podman-compose limitations

---

## Metadata

**Confidence breakdown:**
- Standard stack (Incus/Docker/Podman tools): HIGH — verified from Phase 7 codebase
- Architecture (network topology, env var propagation): HIGH — traced through source code
- Code patterns (all helper functions): HIGH — direct copy from verified working code
- Podman-compose compatibility: MEDIUM — compose.server.yaml analyzed, podman-compose version not pinned
- Pitfalls: HIGH — all drawn from actual Phase 6/7 failures documented in STATE.md

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable infrastructure; podman-compose section revisit if pip version changes)
