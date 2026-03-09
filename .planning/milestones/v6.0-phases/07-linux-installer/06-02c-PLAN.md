---
phase: 06-remote-validation
plan: 02c
type: execute
wave: 3
depends_on:
  - 06-02b
files_modified:
  - puppeteer/installer/install_universal.sh
  - mop_validation/scripts/test_installer_lxc.py
autonomous: false
requirements:
  - REM-03c
  - REM-03e
  - REM-03f

must_haves:
  truths:
    - "The installer runs to completion without jq installed, using only grep/sed for CA extraction"
    - "The installer exits 1 with a clear error message when neither Docker nor Podman is present"
    - "The --platform flag prevents the interactive runtime prompt from hanging incus exec"
    - "Non-root execution skips CA install but installer still downloads compose and starts containers"
  artifacts:
    - path: "puppeteer/installer/install_universal.sh"
      provides: "Installer with hardened grep/sed fallback and confirmed no-runtime error path"
  key_links:
    - from: "install_universal.sh"
      to: "CA extraction (jq branch)"
      via: "command -v jq"
      pattern: "command -v jq"
    - from: "install_universal.sh"
      to: "CA extraction (grep/sed fallback)"
      via: "grep -o '\"ca\":\"[^\"]*\"'"
      pattern: "grep.*ca.*cut.*sed"
---

<objective>
Validate three edge cases in install_universal.sh: (1) jq absent — grep/sed fallback must extract CA
correctly, (2) no container runtime — installer must fail cleanly with a useful error, (3) non-root
execution — CA install is skipped but install continues via --cacert fallback. Fix any bugs found.

Purpose: Edge cases are where production installs break. The grep/sed fallback is documented as fragile
in the research. A hang on the interactive prompt would block non-interactive CI pipelines. These tests
prove the installer is robust, not just happy-path functional.

Output: All three edge-case REM-03 requirements confirmed. install_universal.sh patched if grep/sed
fallback is broken. Test harness extended with edge-case scenarios.
</objective>

<execution_context>
@/home/thomas/.claude/get-shit-done/workflows/execute-plan.md
@/home/thomas/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/phases/06-remote-validation/06-02-RESEARCH.md
@.planning/phases/06-remote-validation/06-02b-SUMMARY.md

<interfaces>
<!-- Key facts for edge case testing. Derived from research. -->

Test container: mop-test-node (managed by manage_node.py)
Provisioned with: podman (but NOT jq, NOT docker)

EDGE CASE 1 — jq absent (REM-03c):
The LXC container from manage_node.py has podman but NOT jq. This means the happy path test
in 06-02b either:
  (a) already exercised the grep/sed path (if jq was not installed), or
  (b) installed jq manually to work around it.
In this plan: run a dedicated test WITHOUT jq in PATH to prove the grep/sed path.

The grep/sed fallback (from install_universal.sh lines 162-163):
```bash
CA_CONTENT=$(echo "$JSON_PAYLOAD" | grep -o '"ca":"[^"]*"' | cut -d'"' -f4 | sed 's/\\n/\n/g')
```
Known fragility: The CA PEM is a multi-line string encoded as \n in JSON. The grep pattern
matches only if there's no whitespace around the colon in the JSON. The base64-decoded token
should produce compact JSON (no whitespace), so this should work — but must be confirmed.

If CA_CONTENT is empty after the grep/sed, the fix is to improve the grep pattern or use
python3 (which IS available on Ubuntu 24.04) as a jq replacement:
```bash
CA_CONTENT=$(echo "$JSON_PAYLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ca',''))")
```
This is more robust than grep/sed and python3 is always available on Ubuntu.

EDGE CASE 2 — no runtime (REM-03e):
Needs a bare container without podman or docker. Use:
```bash
incus launch images:ubuntu/24.04 mop-bare-node -c security.nesting=true
incus exec mop-bare-node -- bash /tmp/install_universal.sh --platform docker
```
Expected: exit code 1, stderr contains "Docker is not installed."
The --platform docker flag skips the interactive prompt but triggers the platform validation check.

EDGE CASE 3 — non-root execution (REM-03b alternate):
Run installer as the ubuntu user (not root) — manage_node.py's default is ubuntu user.
Expected:
  - install_ca() prints "Warning: Not running as root. Skipping system CA installation."
  - Installer continues
  - curl uses --cacert bootstrap_ca.crt (the file-based cert, not system trust store)
  - Compose is downloaded, podman-compose up starts the container
This verifies the installer degrades gracefully when not root.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Test and fix jq-absent CA extraction (REM-03c)</name>
  <files>puppeteer/installer/install_universal.sh, mop_validation/scripts/test_installer_lxc.py</files>
  <action>
    Run a dedicated test verifying the grep/sed CA extraction path, then fix it if broken.

    **Step 1: Provision a fresh LXC container and verify jq is absent:**
    ```bash
    python3 /home/thomas/Development/master_of_puppets/.agent/skills/manage-test-nodes/scripts/manage_node.py
    incus exec mop-test-node -- which jq && echo "jq present — remove it" || echo "jq absent — good"
    ```
    If jq is present (e.g., installed in 06-02b as a workaround): remove it:
    ```bash
    incus exec mop-test-node -- apt-get remove -y jq
    ```

    **Step 2: Get a JOIN_TOKEN from the live stack:**
    Read ADMIN_PASSWORD from /home/thomas/Development/mop_validation/secrets.env.
    ```bash
    TOKEN=$(curl -sSfk -X POST https://192.168.50.148:8001/auth/login \
      -H "Content-Type: application/json" \
      -d "{\"username\":\"admin\",\"password\":\"$ADMIN_PASSWORD\"}" \
      | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
    JOIN_TOKEN=$(curl -sSfk -H "Authorization: Bearer $TOKEN" \
      https://192.168.50.148:8001/api/node/token \
      | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
    ```

    **Step 3: Test CA extraction manually inside the container (without running full installer):**
    Write a test script that only runs the token parsing logic:
    ```bash
    incus exec mop-test-node -- bash -c "
      JSON_PAYLOAD=\$(echo '$JOIN_TOKEN' | base64 -d 2>/dev/null)
      CA_CONTENT=\$(echo \"\$JSON_PAYLOAD\" | grep -o '\"ca\":\"[^\"]*\"' | cut -d'\"' -f4 | sed 's/\\\\n/\\n/g')
      if [[ -z \"\$CA_CONTENT\" ]]; then
        echo 'FAIL: grep/sed extracted empty CA'
        exit 1
      else
        echo \"PASS: CA extracted, length=\${#CA_CONTENT}\"
      fi
    "
    ```

    **If grep/sed extraction fails (empty CA_CONTENT):**
    Update install_universal.sh to use python3 as the fallback instead of grep/sed:
    ```bash
    else
        # Fallback: use python3 (available on all modern Linux, more reliable than grep/sed)
        CA_CONTENT=$(echo "$JSON_PAYLOAD" | python3 -c \
            "import sys, json; d = json.loads(sys.stdin.read()); print(d.get('ca', ''))" 2>/dev/null || \
            echo "$JSON_PAYLOAD" | grep -o '"ca":"[^"]*"' | cut -d'"' -f4 | sed 's/\\n/\n/g')
    fi
    ```
    This tries python3 first (more robust), then falls back to grep/sed if python3 is absent.
    python3 is installed on Ubuntu 24.04 by default AND by manage_node.py.

    **Step 4: Run the full installer without jq to confirm end-to-end:**
    ```bash
    incus file push /home/thomas/Development/master_of_puppets/puppeteer/installer/install_universal.sh \
      mop-test-node/tmp/install_universal.sh
    incus exec mop-test-node -- bash /tmp/install_universal.sh \
      --token "$JOIN_TOKEN" \
      --server "https://192.168.50.148:8001" \
      --platform podman
    ```
    Assert exit code 0 and heartbeat visible in GET /nodes.

    **Step 5: Add a `--test-jq-fallback` flag or a `jq_fallback` test case to test_installer_lxc.py:**
    Add a second test scenario to the harness that removes jq and re-runs the installer.
    The harness should report REM-03c: PASS or FAIL.

    **Teardown:**
    ```bash
    python3 /home/thomas/Development/master_of_puppets/.agent/skills/manage-test-nodes/scripts/manage_node.py stop
    ```
  </action>
  <verify>
    <automated>incus exec mop-test-node -- which jq 2>/dev/null && echo "jq present" || echo "jq absent — correct for test"</automated>
  </verify>
  <done>
    CA extraction succeeds without jq present.
    Full installer exits 0 without jq.
    If grep/sed was broken, install_universal.sh now uses python3 as primary non-jq fallback.
    REM-03c is marked PASS in test output.
    LXC container torn down.
  </done>
</task>

<task type="auto">
  <name>Task 2: Test no-runtime error path and non-root behavior (REM-03e + REM-03b alt)</name>
  <files>mop_validation/scripts/test_installer_lxc.py</files>
  <action>
    Run two additional edge case scenarios.

    **Scenario A: No container runtime (REM-03e)**

    Launch a bare (non-provisioned) Ubuntu container — no podman, no docker:
    ```bash
    incus launch images:ubuntu/24.04 mop-bare-node -c security.nesting=true
    # Wait for it to start (~5s)
    sleep 5
    ```
    Do NOT run manage_node.py — we want a truly bare container.

    Get a fresh JOIN_TOKEN (same method as Task 1, Step 2).

    Copy installer into bare container:
    ```bash
    incus file push /home/thomas/.../install_universal.sh mop-bare-node/tmp/install_universal.sh
    ```

    Run installer with --platform docker (skip interactive prompt, trigger platform check):
    ```bash
    incus exec mop-bare-node -- bash /tmp/install_universal.sh \
      --token "$JOIN_TOKEN" \
      --server "https://192.168.50.148:8001" \
      --platform docker
    ```

    Assert:
    - Exit code is 1 (non-zero)
    - Output contains "Docker is not installed." or "Neither Docker nor Podman found."

    Cleanup:
    ```bash
    incus delete mop-bare-node --force
    ```

    **Scenario B: Non-root installer run (REM-03b alternate)**

    Provision a normal test node:
    ```bash
    python3 /home/thomas/.../manage_node.py
    ```

    Install podman-compose, configure insecure registry (same as 06-02b setup).

    Run installer as the ubuntu user (NOT root):
    ```bash
    incus exec mop-test-node --user 1000 -- bash /tmp/install_universal.sh \
      --token "$JOIN_TOKEN" \
      --server "https://192.168.50.148:8001" \
      --platform podman
    ```
    Note: `--user 1000` runs as uid 1000 (ubuntu). If incus exec doesn't support --user,
    use: `incus exec mop-test-node -- sudo -u ubuntu bash /tmp/install_universal.sh ...`

    Assert:
    - Output contains "Warning: Not running as root. Skipping system CA installation."
    - CA file does NOT exist at /usr/local/share/ca-certificates/mop-root.crt
    - Installer still exits 0 (continues using --cacert bootstrap_ca.crt for curl)
    - Heartbeat appears in /nodes (installer still works non-root)

    The non-root heartbeat verifies the --cacert fallback path is functional even without system CA trust.

    **Add both scenarios to test_installer_lxc.py:**
    Add a `run_edge_case_tests()` function that executes Scenario A and Scenario B.
    Report results as REM-03e and REM-03b-nonroot.

    Teardown:
    ```bash
    python3 /home/thomas/.../manage_node.py stop
    ```
  </action>
  <verify>
    <automated>python3 /home/thomas/Development/mop_validation/scripts/test_installer_lxc.py 2>&1 | grep -E "REM-03e|REM-03b-nonroot|PASS|FAIL" | head -10</automated>
  </verify>
  <done>
    REM-03e: installer exits 1 with clear error when no runtime installed.
    REM-03b-nonroot: installer exits 0 with CA skip warning; heartbeat still appears.
    Both scenarios added to test_installer_lxc.py as automated test cases.
    All LXC containers (mop-test-node, mop-bare-node) torn down after tests.
  </done>
</task>

</tasks>

<verification>
After both tasks complete:
1. REM-03c: Running installer without jq exits 0 and CA is correctly extracted
2. REM-03e: Running installer with no runtime exits 1 with readable error message
3. REM-03b-nonroot: Non-root installer run prints skip warning but still enrolls node
4. test_installer_lxc.py covers all 6 REM-03 sub-requirements
5. All LXC containers cleaned up
6. install_universal.sh changes (if any) are minimal and commented

Run final summary verification:
```bash
python3 /home/thomas/Development/mop_validation/scripts/test_installer_lxc.py --summary-only 2>&1
```
</verification>

<success_criteria>
- All 6 REM-03 sub-requirements have automated test coverage in test_installer_lxc.py
- grep/sed fallback works OR is replaced by python3 fallback (documented in code comment)
- Installer cleanly errors when no runtime present (not a hang, not a confusing traceback)
- Non-root run degrades gracefully (CA skip warning + continues via --cacert)
- install_universal.sh passes `bash -n` syntax check after any changes
</success_criteria>

<output>
After completion, create `.planning/phases/06-remote-validation/06-02c-SUMMARY.md`

Include in summary:
- Results for each of the 6 REM-03 sub-requirements (PASS/FAIL/FIXED)
- List of all changes made to install_universal.sh with rationale
- Final state of test_installer_lxc.py test coverage
- Any findings relevant to Phase 3 (Cross-Network Validation)
</output>
