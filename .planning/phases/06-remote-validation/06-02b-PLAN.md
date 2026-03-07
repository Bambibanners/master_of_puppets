---
phase: 06-remote-validation
plan: 02b
type: execute
wave: 2
depends_on:
  - 06-02a
files_modified:
  - puppeteer/installer/install_universal.sh
  - puppeteer/agent_service/main.py
autonomous: false
requirements:
  - REM-03
  - REM-03a
  - REM-03b
  - REM-03d
  - REM-03f

must_haves:
  truths:
    - "Running install_universal.sh on fresh Ubuntu 24.04 (via LXC) exits 0 with no errors"
    - "After installer run, the MOP Root CA exists at /usr/local/share/ca-certificates/mop-root.crt inside the container"
    - "The installed node sends a heartbeat that appears in GET /nodes within 60 seconds"
    - "The installer completes within the 120-second timeout (--platform podman prevents interactive hang)"
  artifacts:
    - path: "puppeteer/installer/install_universal.sh"
      provides: "Fixed installer that references a registry-accessible image"
      contains: "5000"
    - path: "puppeteer/agent_service/main.py"
      provides: "Compose generator that uses a registry-accessible image reference"
  key_links:
    - from: "install_universal.sh"
      to: "GET /api/node/compose"
      via: "curl with --cacert bootstrap_ca.crt"
      pattern: "curl.*cacert.*COMPOSE_URL"
    - from: "node-compose.yaml (generated)"
      to: "192.168.50.148:5000/puppet-node:latest"
      via: "podman-compose up"
      pattern: "image:.*5000.*puppet-node"
---

<objective>
Run the happy path installer test: provision an ephemeral Incus LXC container, execute
install_universal.sh against the live stack, and verify successful CA install + node enrollment.
Fix any installer or compose-generation bugs discovered during the run.

Purpose: This is the primary validation of REM-03. A clean run proves the installer is production-ready
for fresh Ubuntu 24.04 environments. Bugs found here are fixed before the edge-case tests in Wave 3.

Output: Confirmed heartbeat from an LXC-provisioned node. install_universal.sh and/or main.py patched
if the image reference or any other blocker is discovered during the run.
</objective>

<execution_context>
@/home/thomas/.claude/get-shit-done/workflows/execute-plan.md
@/home/thomas/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/06-remote-validation/06-CONTEXT.md
@.planning/phases/06-remote-validation/06-02-RESEARCH.md
@.planning/phases/06-remote-validation/06-02a-SUMMARY.md

<interfaces>
<!-- Key facts for this wave. No exploration needed. -->

Host LAN IP: 192.168.50.148
LXC container name: mop-test-node (managed by manage_node.py)
Local registry: localhost:5000 (accessible from LXC as 192.168.50.148:5000)
Test harness: /home/thomas/Development/mop_validation/scripts/test_installer_lxc.py

KNOWN BLOCKER: main.py compose template uses `localhost/master-of-puppets-node:latest`.
Inside the LXC container, this image doesn't exist. The fix is to update the image reference
in main.py's compose template to `192.168.50.148:5000/puppet-node:latest`.

From main.py (lines ~365-380):
```python
compose_content = f"""
services:
  puppet:
    image: localhost/master-of-puppets-node:latest   # <-- THIS IS THE BLOCKER
    container_name: puppet-node
    network_mode: host
    environment:
      - AGENT_URL={os.getenv("AGENT_URL", "https://localhost:8001")}
      - JOIN_TOKEN={token}
    ...
"""
```
The image should be configurable via an env var (e.g., NODE_IMAGE) with a default that
works for the LXC scenario. Best approach: read from env var `NODE_IMAGE` with default
`localhost/master-of-puppets-node:latest`. In puppeteer/.env, set:
  NODE_IMAGE=192.168.50.148:5000/puppet-node:latest

This avoids hardcoding a specific IP in the source code while making it configurable.

INSECURE CURL FALLBACK: If the CA cert verify fails, installer falls back to curl -k.
Test must verify the secure path was taken (not the fallback).
Detection: Check installer stdout for "SSL verification" errors before fallback line.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Fix compose image reference to use configurable NODE_IMAGE env var</name>
  <files>puppeteer/agent_service/main.py, puppeteer/.env</files>
  <action>
    The compose template in main.py hardcodes `localhost/master-of-puppets-node:latest`. This image
    is unavailable inside LXC containers. Fix by making the image reference configurable.

    **In puppeteer/agent_service/main.py:**
    Find the `get_node_compose` function (or equivalent that generates the compose YAML).
    Change the image line from:
    ```python
    image: localhost/master-of-puppets-node:latest
    ```
    to:
    ```python
    image: {os.getenv("NODE_IMAGE", "localhost/master-of-puppets-node:latest")}
    ```

    **In puppeteer/.env:**
    Add the line:
    ```
    NODE_IMAGE=192.168.50.148:5000/puppet-node:latest
    ```

    After editing .env, restart the agent container:
    ```bash
    docker compose -f puppeteer/compose.server.yaml up -d --no-build agent
    ```

    Verify by calling the compose endpoint and checking the image field:
    ```bash
    TOKEN=$(curl -sSf -k -X POST https://192.168.50.148:8001/auth/login \
      -H "Content-Type: application/json" \
      -d '{"username":"admin","password":"<from secrets.env>"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
    JOIN_TOKEN=$(curl -sSf -k -H "Authorization: Bearer $TOKEN" \
      https://192.168.50.148:8001/api/node/token | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
    curl -sSf -k "https://192.168.50.148:8001/api/node/compose?token=$JOIN_TOKEN&platform=podman" | grep image
    ```
    Expected output: `image: 192.168.50.148:5000/puppet-node:latest`

    Read ADMIN_PASSWORD from /home/thomas/Development/mop_validation/secrets.env to use in the curl.
  </action>
  <verify>
    <manual>
      Read ADMIN_PASSWORD from mop_validation/secrets.env, then:
        TOKEN=$(curl -sSfk -X POST https://192.168.50.148:8001/auth/login \
          -H "Content-Type: application/json" \
          -d '{"username":"admin","password":"PASSWORD"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
        JOIN=$(curl -sSfk -H "Authorization: Bearer $TOKEN" \
          https://192.168.50.148:8001/api/node/token | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
        curl -sSfk "https://192.168.50.148:8001/api/node/compose?token=$JOIN&platform=podman" | grep image
      Expected: line containing "5000" (i.e. 192.168.50.148:5000/puppet-node:latest)
    </manual>
  </verify>
  <done>
    The generated node-compose.yaml contains an image reference to 192.168.50.148:5000/puppet-node:latest.
    Verified by calling the compose endpoint with a valid token and grepping the response.
  </done>
</task>

<task type="auto">
  <name>Task 2: Run happy path installer test and fix any discovered issues</name>
  <files>puppeteer/installer/install_universal.sh</files>
  <action>
    Run the full test harness against the live stack. Observe and fix any failures.

    **Step 1: Execute the test harness:**
    ```bash
    python3 /home/thomas/Development/mop_validation/scripts/test_installer_lxc.py
    ```
    The script provisions an LXC container, installs podman-compose and registry config, copies the
    installer, runs it as root with `--platform podman`, and checks all REM-03a/b/d/f assertions.

    **Step 2: Diagnose and fix failures. Common expected failures and fixes:**

    **Issue: "podman-compose: command not found"**
    Fix: The test harness (06-02a) should install podman-compose before running. If the harness didn't
    do it, add `incus exec mop-test-node -- pip3 install podman-compose` before the installer call.
    Then update test_installer_lxc.py.

    **Issue: "Could not extract CA from token" (jq fallback)**
    This is covered in Wave 3 (06-02c). In the happy path, jq MAY be absent since manage_node.py
    doesn't install it. If CA extraction fails, install jq first to prove the primary path works:
    `incus exec mop-test-node -- apt-get install -y jq`
    Note this as a finding for 06-02c (jq fallback testing).

    **Issue: "curl: (60) SSL certificate problem" then fallback to -k**
    Investigate: was the CA installed correctly? Check:
    ```bash
    incus exec mop-test-node -- ls /usr/local/share/ca-certificates/mop-root.crt
    incus exec mop-test-node -- update-ca-certificates --fresh 2>&1
    incus exec mop-test-node -- curl -sSf https://192.168.50.148:8001/api/node/token
    ```
    Fix: install_universal.sh's `install_ca()` runs `update-ca-certificates` but the CA copy must
    happen before subsequent curls. This is already the correct order in the script.
    If it's still falling back to `-k`, check whether the server cert SAN includes `192.168.50.148`.
    Run: `openssl s_client -connect 192.168.50.148:8001 2>/dev/null | openssl x509 -noout -text | grep -A1 "Subject Alternative"`
    If the LAN IP is not in the SAN, this is a Phase 1 issue — note as a finding.

    **Issue: podman-compose fails to pull the image**
    Check: `incus exec mop-test-node -- cat /etc/containers/registries.conf.d/local-registry.conf`
    If the insecure registry config is missing, add it manually and re-run podman-compose.

    **Issue: Heartbeat not appearing in /nodes**
    Check node container logs: `incus exec mop-test-node -- podman logs puppet-node`
    Common causes: AGENT_URL wrong in generated compose, CA trust failure in node.py, network_mode: host
    not bridging to the host IP.

    **After ALL fixes are applied:**
    Re-run the test harness. All REM-03a/b/d/f checks must pass.
    The test script will print a summary table. Paste results into the SUMMARY.

    The test harness handles teardown automatically (try/finally).
  </action>
  <verify>
    <automated>python3 /home/thomas/Development/mop_validation/scripts/test_installer_lxc.py 2>&1 | tail -20</automated>
  </verify>
  <done>
    Test harness runs and reports PASS for:
    - REM-03a: installer exit code 0
    - REM-03b: CA file present at /usr/local/share/ca-certificates/mop-root.crt
    - REM-03d: heartbeat in GET /nodes within 60s
    - REM-03f: completed without 120s timeout

    Any install_universal.sh bugs found are fixed (with clear comments noting what was changed and why).
    LXC container is torn down after the run.
  </done>
</task>

</tasks>

<verification>
After both tasks complete:
1. `curl -sSfk "https://192.168.50.148:8001/api/node/compose?token=...&platform=podman" | grep image` contains "5000"
2. Test harness reports all 4 assertions PASS
3. GET /nodes (authenticated) returns at least one node with recent last_seen timestamp
4. LXC container `mop-test-node` is deleted (incus list shows nothing)
</verification>

<success_criteria>
- main.py compose template reads NODE_IMAGE from env var
- NODE_IMAGE=192.168.50.148:5000/puppet-node:latest set in puppeteer/.env
- Fresh Ubuntu 24.04 LXC container successfully enrolls as a MOP node
- CA is installed to system trust store during installer run (root execution confirmed)
- Heartbeat appears in /nodes API within 60s of installer completion
</success_criteria>

<output>
After completion, create `.planning/phases/06-remote-validation/06-02b-SUMMARY.md`

Include in summary:
- Which failures were encountered and how they were fixed
- Any findings about edge cases (jq fallback, insecure curl, SAN coverage) to carry into 06-02c
- Final test harness output (pass/fail table)
</output>
