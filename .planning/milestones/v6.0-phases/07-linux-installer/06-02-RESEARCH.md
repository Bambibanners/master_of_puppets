# Phase 06-02: Linux Universal Installer - Research

**Researched:** 2026-03-07
**Domain:** Bash installer validation, Incus LXC ephemeral containers, mTLS node enrollment
**Confidence:** HIGH

## Summary

This phase validates `puppeteer/installer/install_universal.sh` on a fresh Ubuntu 24.04 environment
using ephemeral Incus LXC containers. Phase 1 (Remote Server Deployment) has already hardened the
installer by adding `install_ca()` and fixing `SERVER_URL` handling — this phase now executes the
validation to prove those fixes work end-to-end on a genuinely fresh Linux system.

The installer script is a deployment orchestrator that: (1) decodes the JOIN_TOKEN to extract the Root
CA, (2) installs the CA into the OS trust store, (3) downloads a compose file from the server using
that CA, and (4) launches the node container. The critical risk is that each step assumes the previous
one succeeded — there are several hardcoded assumptions and silent fallbacks that need probing on a
fresh system where curl, jq, docker, and podman may not be pre-installed.

The Incus LXC skill is ideal for this: the `manage_node.py` script provisions Ubuntu 24.04 containers
with their own IP, SSH access, and nested Podman support in approximately 30 seconds. The testing
strategy should use `incus exec` to run the installer inside the container, then SSH in to verify the
enrollment result.

**Primary recommendation:** Validate the installer in a reproducible, isolated Incus container by
running it end-to-end against the live local stack, checking each prerequisite gap individually, and
confirming a successful heartbeat appears in the dashboard.

## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|---|---|---|---|
| `incus` | 6.22 (confirmed on host) | Ephemeral Ubuntu 24.04 LXC containers | Installed, user in `incus-admin` group, no sudo required |
| `manage_node.py` | project skill | Provision/teardown test node, update secrets.env | Already encapsulates all Incus lifecycle |
| `install_universal.sh` | v1.0 | Script under test | The subject of this phase |
| `bash` | Ubuntu default | Script interpreter | Install script requires bash, not sh |
| `jq` | 1.6 (Ubuntu 24.04) | Token JSON extraction | Script uses jq if available, falls back to grep/sed |
| `curl` | 8.x (Ubuntu 24.04) | Download compose + key | Required, not guaranteed on minimal images |

### Ubuntu 24.04 Package Availability (fresh image)
Ubuntu 24.04 minimal (Incus `images:ubuntu/24.04`) ships with:
- **curl**: Present by default
- **jq**: NOT present by default — must be `apt-get install jq`
- **docker**: NOT present
- **podman**: NOT present (but installed by `manage_node.py` during provisioning)
- **python3**: Present by default
- **update-ca-certificates**: Present (part of `ca-certificates` package, default)

The Incus provisioning script (`manage_node.py`) explicitly runs `apt-get install -y podman openssh-server python3 python3-pip sudo` — so the container will have Podman but NOT jq or docker-compose/docker.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|---|---|---|
| Incus LXC | Docker-in-Docker | LXC gives real Ubuntu with proper machine-id, SSH, and clean apt — much more realistic |
| Incus LXC | Real remote VM | LXC is faster (< 30 sec) and ephemeral; real VM takes minutes and costs money |
| `incus exec` | SSH for test commands | `incus exec` is faster for automation; SSH is better for interactive debugging |

## Architecture Patterns

### Recommended Test Structure

```
Phase 2 Test Flow:
1. Launch Incus node (manage_node.py) — already provisioned with Podman
2. Copy install_universal.sh into container
3. Run installer with --token and --server flags
4. Assert: CA written to /usr/local/share/ca-certificates/mop-root.crt
5. Assert: node-compose.yaml downloaded
6. Assert: Podman containers started (podman ps inside container)
7. Assert: Heartbeat appears in MOP API (/nodes endpoint)
8. Teardown: manage_node.py stop
```

### Pattern 1: Installer Test via incus exec
**What:** Execute the installer inside the LXC container non-interactively
**When to use:** Automated, reproducible runs without interactive prompts
**Key flag:** `--platform podman` eliminates the interactive `[1/2] Choose runtime` prompt
**Example:**
```bash
# Copy script into container
incus file push /path/to/install_universal.sh mop-test-node/tmp/install_universal.sh
incus exec mop-test-node -- bash /tmp/install_universal.sh \
  --token "$JOIN_TOKEN" \
  --server "https://$SERVER_IP:8001" \
  --platform podman
```

### Pattern 2: Dependency Gap Testing
**What:** Run installer on a truly minimal container (no Podman pre-installed) to validate error paths
**When to use:** Testing the "neither Docker nor Podman found" error path
**Example:**
```bash
# Launch bare container without provisioning
incus launch images:ubuntu/24.04 mop-bare-node -c security.nesting=true
incus exec mop-bare-node -- bash /tmp/install_universal.sh --platform docker
# Expect: clean error "Neither Docker nor Podman found. Please install one first."
```

### Pattern 3: CA Trust Verification
**What:** Confirm the CA was installed into the system trust store, then curl the server without --cacert
**When to use:** After successful install_ca() call
**Example:**
```bash
incus exec mop-test-node -- curl -sSf "https://$SERVER_IP:8001/system/root-ca" -o /dev/null
# If exit 0: system CA trust is working. If SSL error: CA install failed.
```

### Anti-Patterns to Avoid
- **Non-interactive assumption**: The installer has `read -p "Select runtime [1/2]"` — always pass `--platform` in automated tests or the command will hang waiting for input
- **Running as root blindly**: The `install_ca()` function checks `$EUID -ne 0` and skips silently — tests must use `sudo` or run as root for the CA install step to execute
- **Testing against localhost**: The Incus container has its own IP; `SERVER_URL=https://localhost:8001` will fail inside the container — always pass the host's LAN IP
- **Ignoring the fallback insecure curl**: Line 193 falls back to `curl -k` if CA verification fails — tests must check which curl path was taken, not just whether the file was downloaded

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Fresh Linux environment | Custom Docker containers, chroot | Incus LXC via `manage_node.py` | Real Ubuntu 24.04 with machine-id, SSH, Podman — already available |
| Node IP management | Manual IP discovery | `manage_node.py` auto-updates `secrets.env` | Already handles waiting for IP |
| CA extraction from token | Re-implement base64+jq | The installer script itself | Already has the logic — test the script, don't duplicate it |
| Heartbeat verification | Polling node logs | GET `/nodes` API endpoint | Server records heartbeats; easier to query than parse container logs |

**Key insight:** All infrastructure needed for this validation already exists. The work is almost
entirely execution and observation, not building.

## Common Pitfalls

### Pitfall 1: Interactive Prompt Hang
**What goes wrong:** Installer hits `read -p "Select runtime [1/2]"` when both Docker and Podman exist (Podman is pre-installed by manage_node.py). Script hangs indefinitely in `incus exec`.
**Why it happens:** `incus exec` provides a non-TTY stdin by default, so `read` blocks forever.
**How to avoid:** Always pass `--platform podman` when running non-interactively.
**Warning signs:** `incus exec` command never returns.

### Pitfall 2: ROOT_CA_PATH Hardcoded Windows Path in node.py
**What goes wrong:** `ROOT_CA_PATH = os.getenv("ROOT_CA_PATH", "c:/Development/Repos/master_of_puppets/ca/certs/root_ca.crt")` — the default is a Windows path. On a fresh Linux container where `ROOT_CA_PATH` env var isn't set, this path doesn't exist. However, `bootstrap_trust()` in node.py overwrites `ROOT_CA_PATH` from the token, so the hardcoded default is only used pre-enrollment. The node-compose.yaml sets `ROOT_CA_PATH=/app/secrets/root_ca.crt` which overrides this — so it's only a problem if the compose file is missing the env var.
**Why it happens:** Legacy default value for Windows dev environment.
**How to avoid:** Verify the downloaded `node-compose.yaml` contains `ROOT_CA_PATH=/app/secrets/root_ca.crt`.
**Warning signs:** Node container logs show SSL verification failing with "file not found" before enrollment.

### Pitfall 3: network_mode: host in Generated Compose
**What goes wrong:** `GET /api/node/compose` generates a compose file with `network_mode: host`. Inside an Incus LXC system container with `security.nesting=true`, host networking may conflict with the container's bridge network, or the Podman container inside LXC won't resolve the AGENT_URL correctly.
**Why it happens:** `network_mode: host` was designed for bare-metal Docker nodes, not nested containers.
**How to avoid:** Verify the AGENT_URL resolves correctly inside the Podman-in-LXC environment. The host's LAN IP should work since LXC containers are on the same bridge network.
**Warning signs:** Node starts but never connects — heartbeat never appears in dashboard.

### Pitfall 4: CA Install Skipped Silently (Non-Root)
**What goes wrong:** `install_ca()` checks `$EUID -ne 0` and prints "Warning: Not running as root. Skipping system CA installation." The `update-ca-certificates` call is skipped. The subsequent `curl --cacert bootstrap_ca.crt` still works because it uses the file directly, but the system-level trust store is not updated.
**Why it happens:** Installer is run as the `ubuntu` user (non-root) in the Incus container.
**How to avoid:** Run installer with `sudo` or as root in tests that exercise the CA install path. Separate test: run without sudo and verify fallback `--cacert` curl still works.
**Warning signs:** `install_ca()` prints the skip warning but installer continues and succeeds via `--cacert` fallback.

### Pitfall 5: jq Not Available, grep Fallback Fragility
**What goes wrong:** The grep/sed fallback for CA extraction (`grep -o '"ca":"[^"]*"'`) assumes the JSON has no whitespace around the colon and the CA value contains no special characters beyond `\n`. The CA PEM contains forward slashes, plus signs, and equals signs that this regex should handle, but the `\n` to newline conversion via `sed 's/\\n/\n/g'` may behave differently across platforms.
**Why it happens:** jq is not installed on fresh Ubuntu 24.04.
**How to avoid:** Install jq as part of the test setup (or document that jq should be a prerequisite). Test explicitly: run the installer without jq, verify CA extraction succeeds.
**Warning signs:** `CA_CONTENT` is empty → installer exits "Could not extract CA from token."

### Pitfall 6: Insecure Curl Fallback Masks Failures
**What goes wrong:** Line 192-193 of install_universal.sh:
```bash
curl -sSfL --cacert bootstrap_ca.crt "$COMPOSE_URL" -o node-compose.yaml || \
    curl -sSfLk "$COMPOSE_URL" -o node-compose.yaml
```
If the CA-verified curl fails (wrong CA, wrong hostname), the script silently falls back to `-k` (insecure). The compose file is downloaded but the TLS validation is bypassed. This would be a security regression.
**Why it happens:** Robustness fallback.
**How to avoid:** In passing tests, verify the secure curl path succeeded (check curl exit code before fallback). Failing tests should check that the CA was the right one.
**Warning signs:** Install "succeeds" but server logs show `tls: certificate verify failed` before the compose download.

### Pitfall 7: Generated Compose Uses localhost/master-of-puppets-node:latest
**What goes wrong:** `GET /api/node/compose` generates a compose file referencing `localhost/master-of-puppets-node:latest`. Inside the Incus container, this image does not exist. Podman will try to pull from Docker Hub (which doesn't have this image) and fail.
**Why it happens:** The image is a locally-built image that exists on the host but not in the LXC container. The node-compose.yaml endpoint hardcodes this image name.
**How to avoid:** Either (a) push the image to a local registry accessible from the LXC container, or (b) build the image inside the LXC container first. Option (a) is simpler: use `localhost:5000` registry that's already used in the project. This is a significant setup prerequisite for the test.
**Warning signs:** `podman-compose up` fails with "Error: short-name resolution failed for localhost/master-of-puppets-node:latest"

## Code Examples

### How install_universal.sh decodes the token (lines 153-174)
```bash
# Source: puppeteer/installer/install_universal.sh
JSON_PAYLOAD=$(echo "$TOKEN" | base64 -d 2>/dev/null || echo "")
if command -v jq &>/dev/null; then
    CA_CONTENT=$(echo "$JSON_PAYLOAD" | jq -r '.ca // empty')
else
    # Fallback: fragile grep
    CA_CONTENT=$(echo "$JSON_PAYLOAD" | grep -o '"ca":"[^"]*"' | cut -d'"' -f4 | sed 's/\\n/\n/g')
fi
echo "$CA_CONTENT" > bootstrap_ca.crt
install_ca
```

### How node.py reads the CA from the token (bootstrap_trust)
```python
# Source: puppets/environment_service/node.py
decoded_bytes = base64.b64decode(top_token)
payload = json.loads(decoded_str, strict=False)
if "t" in payload and "ca" in payload:
    ca_content = payload["ca"]
    with open("secrets/root_ca.crt", "w") as f:
        f.write(ca_content)
    ROOT_CA_PATH = os.path.abspath("secrets/root_ca.crt")
    VERIFY_SSL = ROOT_CA_PATH
    self.join_token = payload["t"]  # Inner token for enrollment
```

### How the compose file is generated (main.py)
```python
# Source: puppeteer/agent_service/main.py lines 365-380
compose_content = f"""
version: '3.8'
services:
  puppet:
    image: localhost/master-of-puppets-node:latest
    container_name: puppet-node
    network_mode: host
    environment:
      - AGENT_URL={os.getenv("AGENT_URL", "https://localhost:8001")}
      - JOIN_TOKEN={token}
      - MOUNT_DATA={mounts if mounts else ""}
      - NODE_TAGS={effective_tags}
    volumes:
      - ./secrets:/app/secrets
    restart: unless-stopped
"""
```

**Critical:** `AGENT_URL` in the generated compose uses the server's `AGENT_URL` env var, which defaults to `https://localhost:8001`. If this env var is not overridden on the server, all enrolled nodes will try to connect to localhost — which is wrong for nodes running on a different machine.

### Test Node Launch Command
```bash
# Source: .agent/skills/manage-test-nodes/scripts/manage_node.py
python3 /home/thomas/Development/master_of_puppets/.agent/skills/manage-test-nodes/scripts/manage_node.py
# Teardown:
python3 /home/thomas/Development/master_of_puppets/.agent/skills/manage-test-nodes/scripts/manage_node.py stop
```

### Verify heartbeat via API
```bash
# After installer runs, check if node registered:
curl -sSf -H "Authorization: Bearer $JWT" \
  "https://localhost:8001/nodes" | jq '.[].node_id'
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Manual compose file maintenance | Server generates compose dynamically at `/api/node/compose` | Phase 1 | Node gets correct JOIN_TOKEN embedded |
| Static CA file mount | Token contains embedded CA (bootstrap_trust) | Sprint 7 | Nodes are self-bootstrapping without pre-staging files |
| No system CA install | `install_ca()` installs to OS trust store | Phase 1 (M6) | Subsequent curl/https calls work without --cacert flag |
| Single CA (mTLS only) | Unified CA (Caddy TLS + mTLS share one root) | Phase 1 (M6) | One CA import covers both dashboard HTTPS and mTLS enrollment |

**Deprecated/outdated:**
- `node-compose.yaml` in `puppets/` directory: This is the local dev compose. The installer downloads a dynamically generated one from the server — the static file is for reference only.
- `ROOT_CA_PATH` default `c:/Development/Repos/...`: Windows dev path, overridden by compose env var and bootstrap_trust. Not a production issue.

## Open Questions

1. **Image availability in LXC containers**
   - What we know: `GET /api/node/compose` generates a compose referencing `localhost/master-of-puppets-node:latest`. This image is on the host machine.
   - What's unclear: The Incus LXC container cannot access the host's local image store. A registry is needed.
   - Recommendation: Test plans must include pushing the node image to the host's local registry (`:5000`) and configuring the LXC container to pull from it. The test setup wave should handle this.

2. **AGENT_URL propagation**
   - What we know: The server's `AGENT_URL` env var is embedded into the generated compose file. If it's `https://localhost:8001`, enrolled nodes from LXC will fail to connect.
   - What's unclear: What is the actual `AGENT_URL` value in the running docker stack on the host?
   - Recommendation: Test plans must verify `AGENT_URL` in the server's `.env` is set to the host's LAN IP, not localhost, before running the installer test.

3. **podman-compose availability**
   - What we know: The installer requires `podman-compose` for Podman deployments (line 133). The `manage_node.py` installs Podman but not podman-compose.
   - What's unclear: Is `podman-compose` installable via apt on Ubuntu 24.04, or does it require pip?
   - Recommendation: Test plan Wave 0 should install `python3-pip` and `pip install podman-compose` inside the container before running the installer, or use `--platform docker` if Docker is available.

## Validation Architecture

`workflow.nyquist_validation` key is absent from `.planning/config.json` — treated as enabled.

### Test Framework
| Property | Value |
|---|---|
| Framework | pytest (backend) + manual bash scripts (installer) |
| Config file | `puppeteer/pytest.ini` (if exists) or default |
| Quick run command | `cd puppeteer && pytest tests/ -x -q` |
| Full suite command | `cd puppeteer && pytest tests/` |

Note: The installer itself is a bash script — validation is primarily integration-level, not unit-level.
A Python test script in `mop_validation/scripts/` is the appropriate home for the test harness.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| REM-03a | installer runs without error on fresh Ubuntu 24.04 | integration | `incus exec mop-test-node -- bash /tmp/install_universal.sh --token $T --server $URL --platform podman` | No — Wave 0 |
| REM-03b | CA is imported to system trust store (when run as root) | integration | `incus exec mop-test-node -- update-ca-certificates --fresh && curl -sSf https://$SERVER_IP/` | No — Wave 0 |
| REM-03c | jq fallback works when jq is not installed | integration | Run installer without jq in PATH; assert CA extracted | No — Wave 0 |
| REM-03d | node container starts and sends heartbeat | integration | `curl -H "Authorization: Bearer $JWT" https://localhost:8001/nodes \| jq length` | No — Wave 0 |
| REM-03e | Clean error when no container runtime present | integration | Run on bare container without Docker/Podman; assert exit 1 + message | No — Wave 0 |
| REM-03f | `--platform podman` prevents interactive prompt | integration | `timeout 30 incus exec mop-test-node -- bash install.sh --platform podman ...`; assert exit 0, not timeout | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `cd puppeteer && pytest tests/ -x -q`
- **Per wave merge:** `cd puppeteer && pytest tests/`
- **Phase gate:** Full backend suite + manual verification of heartbeat in dashboard before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `mop_validation/scripts/test_installer_lxc.py` — covers REM-03a through REM-03f
- [ ] `mop_validation/scripts/setup_installer_test_env.sh` — installs podman-compose, jq inside the LXC node
- [ ] Registry setup task: push `localhost/master-of-puppets-node:latest` to `localhost:5000` on host

## Sources

### Primary (HIGH confidence)
- Direct read of `puppeteer/installer/install_universal.sh` — all code behavior documented from source
- Direct read of `puppets/environment_service/node.py` — enrollment flow, ROOT_CA_PATH, bootstrap_trust
- Direct read of `puppeteer/agent_service/main.py` get_node_compose — compose template confirmed
- Direct read of `.agent/skills/manage-test-nodes/scripts/manage_node.py` — Incus lifecycle, what's pre-installed
- `incus version` command — confirmed Incus 6.22 installed, user in `incus-admin` group

### Secondary (MEDIUM confidence)
- `.planning/phases/06-remote-validation/06-01-SUMMARY.md` — Phase 1 hardening confirmed (install_ca, SERVER_HOSTNAME)
- Ubuntu 24.04 package defaults: jq not in default install is well-established; Podman package available in Ubuntu repos

### Tertiary (LOW confidence)
- `podman-compose` on Ubuntu 24.04: assumed pip-only based on project CLAUDE.md reference — not verified via apt search

## Metadata

**Confidence breakdown:**
- Installer behavior: HIGH — read directly from source
- Incus test harness: HIGH — tool confirmed installed, manage_node.py read in full
- Node enrollment flow: HIGH — node.py read in full
- Image availability issue: HIGH — confirmed by compose template analysis
- Ubuntu 24.04 package defaults: MEDIUM — standard knowledge, not queried live
- podman-compose install method: LOW — not verified against apt

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable domain — bash, Incus, Ubuntu package defaults change slowly)
