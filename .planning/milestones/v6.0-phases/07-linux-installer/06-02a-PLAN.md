---
phase: 06-remote-validation
plan: 02a
type: execute
wave: 1
depends_on: []
files_modified:
  - puppeteer/installer/install_universal.sh
  - mop_validation/scripts/test_installer_lxc.py
autonomous: true
requirements:
  - REM-03
  - REM-03a
  - REM-03b
  - REM-03c
  - REM-03d
  - REM-03e
  - REM-03f

must_haves:
  truths:
    - "The running puppeteer stack has AGENT_URL set to the host LAN IP (192.168.50.148), not localhost"
    - "The node image is accessible at localhost:5000/puppet-node:latest from inside an Incus LXC container"
    - "A Python test harness script exists that can run installer validation inside an LXC container"
    - "podman-compose is installable inside the LXC container via pip"
  artifacts:
    - path: "mop_validation/scripts/test_installer_lxc.py"
      provides: "Test harness that provisions LXC container, runs installer, verifies enrollment"
      exports: []
    - path: "puppeteer/installer/install_universal.sh"
      provides: "Installer with corrected image reference for registry-based pull"
      contains: "localhost:5000"
  key_links:
    - from: "puppeteer/agent_service/main.py"
      to: "AGENT_URL env var"
      via: "compose template generation"
      pattern: "os.getenv.*AGENT_URL"
    - from: "mop_validation/scripts/test_installer_lxc.py"
      to: "manage_node.py"
      via: "subprocess call"
      pattern: "manage_node.py"
---

<objective>
Set up the prerequisites for installer validation: fix AGENT_URL propagation in the running stack, push
the node image to the local registry so LXC containers can pull it, and write the Python test harness
that later plans will use to drive installer runs inside ephemeral LXC containers.

Purpose: Without these prerequisites, every installer test will fail silently — nodes will start but
connect to localhost instead of the host, and podman-compose up will fail because the image doesn't
exist in a registry the LXC container can reach.

Output: Working registry endpoint at localhost:5000 with the node image pushed; AGENT_URL set to LAN
IP in the running stack; mop_validation/scripts/test_installer_lxc.py test harness ready.
</objective>

<execution_context>
@/home/thomas/.claude/get-shit-done/workflows/execute-plan.md
@/home/thomas/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/06-remote-validation/06-CONTEXT.md
@.planning/phases/06-remote-validation/06-02-RESEARCH.md
@.planning/phases/06-remote-validation/06-01-SUMMARY.md

<interfaces>
<!-- Key facts extracted from codebase and environment. No exploration needed. -->

Host LAN IP: 192.168.50.148
Running stack containers: puppeteer-agent-1, puppeteer-cert-manager-1, puppeteer-dashboard-1
AGENT_URL: currently NOT set in running container (defaults to https://localhost:8001 — WRONG for LXC)

From puppeteer/agent_service/main.py (compose generation):
```python
compose_content = f"""
services:
  puppet:
    image: localhost/master-of-puppets-node:latest
    ...
    environment:
      - AGENT_URL={os.getenv("AGENT_URL", "https://localhost:8001")}
      - JOIN_TOKEN={token}
    ...
"""
```
The AGENT_URL must be set to https://192.168.50.148:8001 in puppeteer/.env AND the container must be
restarted to pick it up.

From puppeteer/compose.server.yaml (or docker compose config):
The agent service reads from puppeteer/.env. Add AGENT_URL=https://192.168.50.168:8001 there.

Node image: localhost/master-of-puppets-node:latest (exists on host, built by Foundry)
Registry: localhost:5000 is already used by the project (puppeteer/compose.server.yaml has a registry service)

From manage_node.py:
- NODE_NAME = "mop-test-node"
- IMAGE = "images:ubuntu/24.04"
- setup_node() installs: podman, openssh-server, python3, python3-pip, sudo
- Does NOT install: jq, podman-compose
- Provisions with security.nesting=true (nested Podman works)
- ubuntu user has passwordless sudo

Test harness should live at: /home/thomas/Development/mop_validation/scripts/test_installer_lxc.py
manage_node.py path: /home/thomas/Development/master_of_puppets/.agent/skills/manage-test-nodes/scripts/manage_node.py
installer path: /home/thomas/Development/master_of_puppets/puppeteer/installer/install_universal.sh
secrets.env path: /home/thomas/Development/mop_validation/secrets.env
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix AGENT_URL and push node image to local registry</name>
  <files>puppeteer/.env</files>
  <action>
    Two changes needed before any LXC test can succeed:

    **1. Set AGENT_URL in puppeteer/.env:**
    Read puppeteer/.env (or create if absent). Add or update the line:
    ```
    AGENT_URL=https://192.168.50.148:8001
    ```
    Then restart the agent container so it picks up the new env var:
    ```bash
    docker compose -f puppeteer/compose.server.yaml up -d --no-build agent
    ```
    Verify it took effect:
    ```bash
    docker exec puppeteer-agent-1 printenv AGENT_URL
    ```
    Expected output: `https://192.168.50.148:8001`

    **2. Push node image to local registry:**
    The LXC container cannot reach `localhost/master-of-puppets-node:latest` on the host.
    The local registry at localhost:5000 is reachable from inside LXC (host IP from the bridge).

    Check if registry is running:
    ```bash
    docker ps --format "{{.Names}}" | grep registry || echo "registry not running"
    ```

    If registry is not running, start it:
    ```bash
    docker run -d -p 5000:5000 --restart=always --name registry registry:2
    ```

    Tag and push the node image:
    ```bash
    docker tag localhost/master-of-puppets-node:latest localhost:5000/puppet-node:latest
    docker push localhost:5000/puppet-node:latest
    ```

    Verify it was pushed:
    ```bash
    curl -sSf http://localhost:5000/v2/puppet-node/tags/list
    ```
    Expected: `{"name":"puppet-node","tags":["latest"]}`

    Note: Do NOT modify install_universal.sh or main.py at this stage — the image reference fix
    (from localhost/... to 192.168.50.148:5000/...) will be handled in the installer fixes task
    if needed, or can be addressed by configuring the LXC container's registries.conf to treat
    192.168.50.148:5000 as an insecure registry.
  </action>
  <verify>
    <automated>docker exec puppeteer-agent-1 printenv AGENT_URL | grep -q "192.168.50.148" && echo "PASS: AGENT_URL correct" || echo "FAIL: AGENT_URL not set"</automated>
    <automated>curl -sSf http://localhost:5000/v2/puppet-node/tags/list | grep -q "latest" && echo "PASS: image in registry" || echo "FAIL: image not pushed"</automated>
  </verify>
  <done>
    AGENT_URL=https://192.168.50.148:8001 is confirmed via docker exec.
    curl to localhost:5000/v2/puppet-node/tags/list returns {"tags":["latest"]}.
  </done>
</task>

<task type="auto">
  <name>Task 2: Write LXC installer test harness</name>
  <files>mop_validation/scripts/test_installer_lxc.py</files>
  <action>
    Create /home/thomas/Development/mop_validation/scripts/test_installer_lxc.py — a Python script
    that automates installer validation inside an ephemeral Incus LXC container.

    The script MUST:
    1. Read credentials from /home/thomas/Development/mop_validation/secrets.env
       (ADMIN_PASSWORD, SERVER_URL or derive from AGENT_URL)
    2. Get a JWT via POST /auth/login
    3. Get a JOIN_TOKEN via GET /api/node/token (requires auth)
    4. Provision the LXC container using manage_node.py subprocess call:
       ```
       python3 /home/thomas/Development/master_of_puppets/.agent/skills/manage-test-nodes/scripts/manage_node.py
       ```
    5. Install podman-compose inside the container (NOT pre-installed by manage_node.py):
       ```bash
       incus exec mop-test-node -- pip3 install podman-compose
       ```
    6. Configure Podman in the LXC to allow the insecure local registry:
       Create /etc/containers/registries.conf.d/local-registry.conf inside the container with:
       ```toml
       [[registry]]
       location = "192.168.50.148:5000"
       insecure = true
       ```
       Use `incus exec mop-test-node -- bash -c "mkdir -p /etc/containers/registries.conf.d && cat > /etc/containers/registries.conf.d/local-registry.conf << 'EOF'...EOF"`
    7. Copy install_universal.sh into the container:
       ```bash
       incus file push /home/thomas/Development/master_of_puppets/puppeteer/installer/install_universal.sh mop-test-node/tmp/install_universal.sh
       ```
    8. Run the installer as root inside the container (so CA install path executes):
       ```bash
       incus exec mop-test-node -- bash /tmp/install_universal.sh \
         --token "$JOIN_TOKEN" \
         --server "https://192.168.50.148:8001" \
         --platform podman
       ```
       Capture exit code and stdout/stderr.
    9. Run assertions (report pass/fail for each):
       - **REM-03a**: installer exit code is 0
       - **REM-03b**: CA installed: `incus exec mop-test-node -- test -f /usr/local/share/ca-certificates/mop-root.crt`
       - **REM-03d**: heartbeat received: GET /nodes returns a node with last_seen < 120s ago
       - **REM-03f**: installer completed without timeout (use subprocess timeout=120)
    10. Print a summary table: TEST | RESULT | DETAIL
    11. Teardown the LXC container:
        ```
        python3 /path/to/manage_node.py stop
        ```
        Always teardown even if tests fail (use try/finally).

    The script must NOT hardcode ADMIN_PASSWORD. Read it from secrets.env.
    SERVER base URL for API calls: https://192.168.50.148:8001
    Use `verify=False` for https calls (self-signed cert, CA not in host trust store unless we're testing inside LXC).
    Import: requests, subprocess, json, os, re, time, sys

    The node token endpoint: GET /api/node/token — check main.py to confirm exact path and auth requirements.
    If the compose file references `localhost/master-of-puppets-node:latest`, the installer test will fail
    at `podman-compose up`. The script should detect this case and print a clear diagnosis rather than
    silently timing out. Check the downloaded node-compose.yaml image field after installer downloads it.
  </action>
  <verify>
    <automated>python3 /home/thomas/Development/mop_validation/scripts/test_installer_lxc.py --dry-run 2>&1 | grep -v "Error\|Traceback" | head -5 || python3 -c "import ast; ast.parse(open('/home/thomas/Development/mop_validation/scripts/test_installer_lxc.py').read()); print('syntax OK')"</automated>
  </verify>
  <done>
    File exists at mop_validation/scripts/test_installer_lxc.py.
    Python syntax is valid (ast.parse passes).
    Script has all 11 steps described above.
    Script reads ADMIN_PASSWORD from secrets.env, not hardcoded.
  </done>
</task>

</tasks>

<verification>
After completing both tasks:
1. `docker exec puppeteer-agent-1 printenv AGENT_URL` returns `https://192.168.50.148:8001`
2. `curl -sSf http://localhost:5000/v2/puppet-node/tags/list` returns JSON with "latest" tag
3. `python3 -c "import ast; ast.parse(open('/home/thomas/Development/mop_validation/scripts/test_installer_lxc.py').read()); print('OK')"` prints OK
4. The test harness file references manage_node.py and uses incus exec for all container operations
</verification>

<success_criteria>
- AGENT_URL is set to host LAN IP and verified via docker exec
- Local registry (port 5000) serves the node image
- test_installer_lxc.py exists, is syntactically valid, implements all 11 steps
- No hardcoded passwords in test script
</success_criteria>

<output>
After completion, create `.planning/phases/06-remote-validation/06-02a-SUMMARY.md`
</output>
