---
phase: 06-remote-validation
verified: 2026-03-07T20:30:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Confirm node heartbeat visible in Nodes dashboard view after installer run"
    expected: "New node appears with green/online status within 60s of installer completing"
    why_human: "REM-03d was confirmed via API (GET /nodes) in automated tests; dashboard visual confirmation was not performed"
  - test: "Confirm CA-verified curl (no -k fallback) was the path taken in happy-path test"
    expected: "No 'SSL certificate problem' line in installer output; download proceeds via cacert bootstrap"
    why_human: "Summary states secure curl succeeded, but no automated assertion captures which curl branch ran — only exit code checked"
---

# Phase 06: Remote Validation Verification Report

**Phase Goal:** Validate the Linux universal installer against a fresh Ubuntu 24.04 LXC environment — prove remote node enrollment works end-to-end.
**Verified:** 2026-03-07T20:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Running stack has AGENT_URL set to host LAN IP (not localhost) | VERIFIED | `compose.server.yaml` line 67: `AGENT_URL=${AGENT_URL:-https://localhost:8001}`; `.env` sets `AGENT_URL=https://192.168.50.148:8001`; confirmed via `docker exec puppeteer-agent-1 printenv AGENT_URL` per 06-02a SUMMARY |
| 2 | Node image accessible at localhost:5000/puppet-node:latest from LXC | VERIFIED | Image pushed to registry in commit `22c961c`; registry at 192.168.50.148:5000 accessible from LXC bridge; insecure registry config written inside container |
| 3 | Python test harness `test_installer_lxc.py` exists with all required steps | VERIFIED | File exists at `mop_validation/scripts/test_installer_lxc.py`, 682 lines, syntax valid (ast.parse passes), implements all 11 required steps including try/finally teardown |
| 4 | Installer runs to completion (exit 0) on fresh Ubuntu 24.04 LXC | VERIFIED | 06-02b SUMMARY: REM-03a PASS, exit code 0; node-823aafbd enrolled; commit `0ce9f50` |
| 5 | CA is installed to system trust store when run as root | VERIFIED | 06-02b SUMMARY: REM-03b PASS, `/usr/local/share/ca-certificates/mop-root.crt` found; `install_ca()` in installer confirmed functional |
| 6 | Installer works without jq using python3 + printf fallback | VERIFIED | 06-02c SUMMARY: REM-03c PASS; `printf '%s'` fix applied in commit `6a61fdf`; CA length=586 confirmed extracted; node-2bc860ea enrolled |
| 7 | Installer exits 1 with clear error when no container runtime present | VERIFIED | 06-02c SUMMARY: REM-03e PASS; all 3 paths tested: `--platform docker` exits 1 "Docker is not installed.", auto-detect exits 1 "Neither Docker nor Podman found.", `--platform podman` exits 1 "Podman is not installed." |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `puppeteer/installer/install_universal.sh` | Installer with jq/python3/grep-sed CA extraction, install_ca(), printf fix | VERIFIED | 240 lines, bash -n syntax OK, printf in all 3 CA extraction branches (lines 164, 166, 169), install_ca() function present (lines 39-55), clear error paths for missing runtime |
| `mop_validation/scripts/test_installer_lxc.py` | Test harness with happy path + edge cases, try/finally teardown, no hardcoded passwords | VERIFIED | 682 lines, Python syntax OK, `run_happy_path()` covers REM-03a/b/d/f, `run_edge_case_tests()` covers REM-03c/e/b-nonroot, try/finally teardown in all test flows, ADMIN_PASSWORD read from `secrets.env` only |
| `puppeteer/agent_service/main.py` | Compose generator using NODE_IMAGE env var, AGENT_URL IP in server cert SAN | VERIFIED | Line 508: `image: {os.getenv("NODE_IMAGE", "localhost/master-of-puppets-node:latest")}` confirmed; lines 2454-2463: AGENT_URL host parsed and appended to SAN list |
| `puppeteer/compose.server.yaml` | AGENT_URL and NODE_IMAGE in agent service environment block | VERIFIED | Lines 67-68: `AGENT_URL=${AGENT_URL:-https://localhost:8001}` and `NODE_IMAGE=${NODE_IMAGE:-localhost/master-of-puppets-node:latest}` both present |
| `puppeteer/installer/deploy_server.sh` | Single-script server deployment for remote Linux | VERIFIED | File exists (2.2KB), handles Docker install, .env initialization, SERVER_HOSTNAME propagation, `docker compose up -d --build` |
| `docs/REMOTE_DEPLOYMENT.md` | Remote deployment documentation | VERIFIED | File exists in `docs/` directory |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `install_universal.sh` | CA extraction (jq branch) | `command -v jq` guard | VERIFIED | Line 163: `if command -v jq &>/dev/null` — jq branch present |
| `install_universal.sh` | CA extraction (python3 branch) | `elif command -v python3` | VERIFIED | Line 165: `elif command -v python3 &>/dev/null` — python3 fallback present with `printf '%s'` |
| `install_universal.sh` | CA extraction (grep/sed fallback) | pattern match | VERIFIED | Line 168: last-resort fallback with updated regex and `printf '%s'` |
| `install_universal.sh` | `GET /api/node/compose` | `curl --cacert bootstrap_ca.crt` | VERIFIED | Lines 198-199: secure curl with cacert, insecure fallback only on failure |
| `main.py` compose generator | registry-accessible image | `os.getenv("NODE_IMAGE", ...)` | VERIFIED | Line 508: NODE_IMAGE env var read; `.env` sets `192.168.50.148:5000/puppet-node:latest` |
| `test_installer_lxc.py` | `manage_node.py` | `subprocess.run(["python3", MANAGE_NODE_PY])` | VERIFIED | `provision_test_node()` calls manage_node.py, handles known sudoers exit-1 issue gracefully |
| `compose.server.yaml` agent service | `AGENT_URL` env var | environment block | VERIFIED | Line 67 in compose.server.yaml: `- AGENT_URL=${AGENT_URL:-https://localhost:8001}` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| REM-03 | 06-02a, 06-02b | Linux Universal Installer portable on fresh Debian/Ubuntu | SATISFIED | Installer confirmed working on Ubuntu 24.04 LXC via 06-02b happy path |
| REM-03a | 06-02a, 06-02b | Installer exits 0 without error | SATISFIED | 06-02b SUMMARY: REM-03a PASS, exit code 0 |
| REM-03b | 06-02a, 06-02b, 06-02c | CA imported to system trust store (root run) | SATISFIED | 06-02b SUMMARY: REM-03b PASS, mop-root.crt confirmed; non-root variant confirmed skip-and-continue |
| REM-03c | 06-02a, 06-02c | jq fallback works when jq absent | SATISFIED | 06-02c SUMMARY: REM-03c PASS; printf fix in commit 6a61fdf |
| REM-03d | 06-02a, 06-02b | Node container starts and sends heartbeat | SATISFIED | 06-02b SUMMARY: REM-03d PASS, node-823aafbd appeared within ~5s |
| REM-03e | 06-02c | Clean error when no container runtime present | SATISFIED | 06-02c SUMMARY: REM-03e PASS, all 3 paths tested |
| REM-03f | 06-02a, 06-02b, 06-02c | `--platform` flag prevents interactive hang; completes within timeout | SATISFIED | REM-03f PASS in 06-02b and 06-02c; installer completed in <90s |

**Note on requirements traceability:** REM-03 and sub-requirements (REM-03a through REM-03f) are defined in the phase CONTEXT.md and PLAN frontmatter. They do **not** appear in `.planning/REQUIREMENTS.md` (which defines OUT-*, HIST-*, RETR-*, DEP-*, TAG-*, CICD-*, NOTF-*, HOOK-* IDs for the v1/v2 product roadmap). The remote validation requirements are milestone-level infrastructure concerns that were not formally registered in REQUIREMENTS.md. This is expected for a validation milestone phase rather than a feature phase — no orphaned requirements exist in REQUIREMENTS.md for Phase 06.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `install_universal.sh` | 156 | `echo "$TOKEN" | base64 -d` uses echo for base64 decode | Info | Not a bug — `echo` is used for the raw base64 string (no `\n` interpretation issue at this step); `printf '%s'` is correctly applied only to the JSON payload piped to parsers |
| `install_universal.sh` | 198-199 | Silent insecure curl fallback (`curl -k`) | Warning | If CA installation fails or server cert SAN is missing the connecting IP, the compose file is downloaded insecurely without any visible failure. This is a known tradeoff documented in 06-02-RESEARCH.md Pitfall 6 |
| `test_installer_lxc.py` | 27-41 | Hardcoded absolute host paths (MANAGE_NODE_PY, INSTALLER_PATH, SECRETS_ENV_PATH) | Warning | Script is not portable across machines; acceptable for a developer test harness in mop_validation |

No blockers found.

---

### Human Verification Required

**These items need manual testing to fully confirm goal achievement:**

#### 1. Node Heartbeat in Dashboard UI

**Test:** After running `python3 mop_validation/scripts/test_installer_lxc.py`, log into the dashboard at `https://192.168.50.148` and navigate to the Nodes view within 60 seconds of installer completion.
**Expected:** A new node appears with an ONLINE status (green indicator), showing the correct node ID and recent `last_seen` timestamp.
**Why human:** REM-03d was confirmed programmatically via `GET /nodes` API in the automated test harness. The visual dashboard confirmation (that the node appears correctly rendered, not just in the API response) has not been performed.

#### 2. Secure Curl Path Verification

**Test:** Run the installer inside an LXC container and capture the full stdout. Search for any "SSL certificate problem" or "curl: (60)" lines before the compose download succeeds.
**Expected:** No SSL fallback message appears — the `--cacert bootstrap_ca.crt` curl succeeds directly.
**Why human:** The 06-02b SUMMARY states "secure curl (no -k fallback)" succeeded, but the automated test harness asserts only exit code and heartbeat, not which curl branch was taken. A reviewer could confirm by checking installer output for the absence of fallback indicators.

---

### Gaps Summary

No gaps. All 7 observable truths are verified, all required artifacts exist and are substantive, all key links are wired. The phase goal — proving that `install_universal.sh` correctly enrolls a remote node from a fresh Ubuntu 24.04 LXC environment — is achieved.

**Root cause bugs fixed during execution (documented for completeness):**
1. `AGENT_URL` not propagated to agent container (compose.server.yaml environment block missing) — fixed in commit `22c961c`
2. `require_permission()` NameError at startup due to ordering in main.py — fixed in commit `b9b5361`
3. Missing imports for WebhookService/TriggerCreate in main.py — fixed in commit `b9b5361`
4. DB schema missing columns added by prior sprints — applied via ALTER TABLE to live DB
5. Installer CA extraction fails without jq due to grep regex space mismatch — fixed by adding python3 fallback in commit `0ce9f50`
6. Server cert SAN missing LAN IP (192.168.50.148) — AGENT_URL host now added to SAN at cert generation time in commit `0ce9f50`
7. `echo "$JSON_PAYLOAD"` corrupts JSON by interpreting `\n` as literal newlines — root cause of all CA extraction failures; fixed to `printf '%s'` in commit `6a61fdf`
8. curl not installed in Ubuntu 24.04 LXC base image — added to `provision_test_node()` in commit `d056f81`

---

_Verified: 2026-03-07T20:30:00Z_
_Verifier: Claude (gsd-verifier)_
