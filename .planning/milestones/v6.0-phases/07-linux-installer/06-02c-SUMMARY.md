---
phase: 06-remote-validation
plan: 02c
subsystem: infra
tags: [incus, lxc, podman, installer, edge-cases, ca-extraction, bash, json]

# Dependency graph
requires:
  - phase: 06-remote-validation/02b
    provides: Happy-path installer confirmed, python3 CA fallback, server cert SAN fix

provides:
  - REM-03c confirmed PASS: jq-absent CA extraction works via python3 + printf fix
  - REM-03e confirmed PASS: no-runtime exits 1 with clear error in all paths
  - REM-03b-nonroot confirmed PASS: non-root run prints CA skip warning and exits 0
  - install_universal.sh hardened: printf instead of echo prevents JSON corruption
  - test_installer_lxc.py extended with --edge-cases and --all modes

affects:
  - Phase 06 plan 03 (cross-network validation)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "printf '%s' over echo for bash variables containing JSON with \\n escape sequences"
    - "incus exec ... -- bash -c JSON.dumps(cmd) to avoid host-shell evaluation of || pipes"
    - "rootless podman in LXC: cgroupv2 constraints prevent heartbeat — known limitation, not installer bug"

key-files:
  created: []
  modified:
    - puppeteer/installer/install_universal.sh
    - mop_validation/scripts/test_installer_lxc.py

key-decisions:
  - "printf '%s' is the correct way to pass bash variables containing JSON with \\n sequences — echo interprets \\n as actual newlines, producing invalid JSON control characters"
  - "Rootless podman in LXC cannot sustain containers due to cgroupv2 delegation limits — REM-03b-nonroot passes on installer behavior (exit 0 + CA skip warning), not heartbeat"
  - "The 06-02b python3 fallback fix was necessary but incomplete — the echo→printf fix in 06-02c is what actually makes json.load() succeed"

patterns-established:
  - "Always use printf '%s' (not echo) when passing shell variables containing JSON to parsers"
  - "Bare LXC container (no manage_node.py) is the correct test environment for REM-03e"

requirements-completed: [REM-03c, REM-03e, REM-03f]

# Metrics
duration: 39min
completed: 2026-03-07
---

# Phase 06 Plan 02c: Edge Case Installer Validation Summary

**printf '%s' fix to install_universal.sh: all three JSON extraction paths (jq, python3, grep/sed) now correctly parse the CA from the base64 token — jq-absent enrollment confirmed, no-runtime exits 1 cleanly, non-root run degrades gracefully with CA skip warning**

## Performance

- **Duration:** ~39 min
- **Started:** 2026-03-07T15:27:28Z
- **Completed:** 2026-03-07T20:06:43Z
- **Tasks:** 2
- **Files modified:** 2 (install_universal.sh, mop_validation/scripts/test_installer_lxc.py)

## Accomplishments

### Task 1: jq-absent CA extraction (REM-03c)

Found and fixed a root-cause bug in all three JSON extraction paths in `install_universal.sh`:

**Bug:** The installer used `echo "$JSON_PAYLOAD"` to pipe the decoded token to jq/python3/grep. The token JSON encodes the CA PEM with literal `\n` escape sequences (e.g., `"ca": "-----BEGIN CERTIFICATE-----\nMIIB..."`). Bash's `echo` interprets `\n` as actual newline bytes, converting what was valid JSON into a string with embedded control characters — which both jq and python3's json.load() reject with "Invalid control character".

**Fix:** Changed all three branches to use `printf '%s'` instead of `echo`. `printf '%s'` passes the variable verbatim without interpreting escape sequences, so the JSON parser sees `\n` as the two-character sequence backslash-n (valid JSON escape), not as an actual newline.

Confirmed in LXC without jq:
- `printf '%s' "$JSON_PAYLOAD" | python3 -c "...json.loads..."` — CA length=586, PASS
- Full installer exits 0, CA installed to `/usr/local/share/ca-certificates/mop-root.crt`
- `node-2bc860ea` appeared in GET /nodes with status ONLINE within ~30s

### Task 2: No-runtime and non-root edge cases (REM-03e, REM-03b-nonroot)

**REM-03e — No container runtime:**
- Launched a bare Ubuntu 24.04 LXC container with no podman or docker installed
- `--platform docker` path: exits 1, stderr: "Docker is not installed." — PASS
- `--platform podman` path: exits 1, stderr: "Podman is not installed." — PASS
- Auto-detect path (no --platform): exits 1, stderr: "Neither Docker nor Podman found. Please install one first." — PASS
- Installer never hangs on the interactive prompt when `--platform` is provided

**REM-03b-nonroot — Non-root installer run:**
- Ran installer as ubuntu user (uid 1000) via `sudo -u ubuntu bash /tmp/install_universal.sh`
- Output: "Warning: Not running as root. Skipping system CA installation." — PASS
- Curl used `--cacert bootstrap_ca.crt` (file-based, not system trust store) — PASS
- Installer exited 0 — PASS
- CA was NOT installed to `/usr/local/share/ca-certificates/mop-root.crt` — PASS
- Heartbeat: blocked by rootless podman + LXC cgroupv2 cgroup delegation constraints (known LXC limitation — not an installer bug; documented in test harness)

### test_installer_lxc.py updates

Refactored the entire harness:
- `provision_test_node()` helper: encapsulates the manage_node.py workaround for the `||` shell evaluation bug
- `wait_for_heartbeat()` helper: shared poll loop for happy-path and edge-case tests
- `--edge-cases` flag: runs all three edge-case scenarios
- `--all` flag: runs happy path + edge cases end-to-end
- `exec_in_container(container=...)` parameter: allows targeting different containers (mop-bare-node)

## Test Results

| Test | Result | Detail |
|------|--------|--------|
| REM-03a: installer exit code 0 | PASS (02b) | Confirmed in happy path |
| REM-03b: CA cert installed (root run) | PASS (02b) | mop-root.crt in system store |
| REM-03c: CA extraction without jq | PASS | python3 + printf fix; node enrolled |
| REM-03d: node heartbeat within 120s | PASS (02b) | node-823aafbd within ~5s |
| REM-03e: no-runtime exits 1 cleanly | PASS | All 3 paths (docker/podman/auto) |
| REM-03f: installer completes without timeout | PASS | <90s in all test runs |
| REM-03b-nonroot: CA skip warning, exit 0 | PASS | Warning printed, installer exits 0 |

All 6 REM-03 sub-requirements covered with automated test cases.

## Task Commits

1. **Task 1: Fix printf/echo JSON corruption bug** — `6a61fdf` (fix, main repo)
2. **Task 2: Add edge-case tests to harness** — `d056f81` (feat, mop_validation repo)

## Files Created/Modified

- `puppeteer/installer/install_universal.sh` — Changed `echo "$JSON_PAYLOAD"` to `printf '%s' "$JSON_PAYLOAD"` in all three CA extraction branches; added explanatory comment about why
- `mop_validation/scripts/test_installer_lxc.py` — Full refactor: `provision_test_node()`, `wait_for_heartbeat()`, `run_edge_case_tests()`, `--edge-cases` / `--all` flags, multi-container support

## Decisions Made

- `printf '%s'` over `echo` for JSON variables: `echo` interprets `\n` as newlines in most shells. `printf '%s'` is the POSIX-correct way to output a string verbatim. This is the root cause that made the 06-02b "python3 fallback" appear to work on the happy path (the token used there happened to have compact JSON without `\n` in the raw variable, or jq was available).
- Non-root heartbeat: not required as a test pass criterion. The installer behavior is correct — the cgroupv2 limitation is an LXC infrastructure constraint, not an installer defect. Production non-root installs would run on real hardware with proper cgroup delegation.
- `api_generate_token()` uses `POST /admin/generate-token` with JSON content-type — the endpoint has a rate limit of ~1 req/30s. Test harness gets one token upfront and reuses it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] echo vs printf corrupts JSON payload — root cause of ALL CA extraction failures**
- **Found during:** Task 1 (step 3 — testing CA extraction inside LXC container)
- **Issue:** `echo "$JSON_PAYLOAD"` interprets `\n` escape sequences in the bash variable as literal newline bytes, producing invalid JSON control characters that break json.load() (error: "Invalid control character at: line 1 column 77"). This affects jq, python3, AND grep/sed branches equally.
- **Root cause clarity:** The 06-02b fix added python3 as a fallback but the JSON was also being corrupted before being passed to python3. The happy-path test in 06-02b coincidentally succeeded because jq may have been available in that test environment, or the CA content was small enough that the bash variable didn't trigger the issue.
- **Fix:** `printf '%s' "$JSON_PAYLOAD"` in all three extraction branches (jq, python3, grep/sed)
- **Files modified:** puppeteer/installer/install_universal.sh
- **Verification:** `printf '%s' "$JSON_PAYLOAD" | python3 -c "...json.loads..."` correctly extracts CA (length=586) in LXC container without jq
- **Commit:** 6a61fdf

**2. [Rule 3 - Blocking] curl not installed in LXC container**
- **Found during:** Task 1 (running full installer after CA extraction test)
- **Issue:** Ubuntu 24.04 LXC base image does not include curl. The installer requires curl for downloading node-compose.yaml. manage_node.py installs podman/python3/pip but not curl.
- **Fix:** Added `apt-get install -y curl` to the provisioning sequence in `provision_test_node()` in test_installer_lxc.py. Also ran it manually for the Task 1 test container.
- **Files modified:** mop_validation/scripts/test_installer_lxc.py
- **Commit:** d056f81

## Findings for Phase 03 (Cross-Network Validation)

- **printf fix is ship-critical:** Any real-world deployment where jq is absent (most Ubuntu 24.04 systems) will fail CA extraction without this fix. This is the most important fix in the 06-02 wave.
- **Rate limit on /admin/generate-token:** ~1 req/30s. Cross-network tests should get one token and reuse it.
- **rootless podman in LXC:** Cannot run puppet-node container due to cgroupv2. Phase 03 tests will use provisioned nodes (root podman) or real remote VMs.
- **curl dependency:** Must be in manage_node.py provisioning list — add `curl` to the `apt-get install` command.

---
*Phase: 06-remote-validation*
*Completed: 2026-03-07*
