---
phase: 06-remote-validation
plan: 02b
subsystem: infra
tags: [incus, lxc, podman, installer, tls, san, ca-trust, enrollment]

# Dependency graph
requires:
  - phase: 06-remote-validation/02a
    provides: LXC test harness, puppet-node image in local registry, AGENT_URL propagation fix

provides:
  - Confirmed happy-path installer run: exit 0, CA installed, node enrolled, heartbeat received
  - install_universal.sh python3 CA extraction fallback (replaces broken grep fallback)
  - Server cert SAN includes AGENT_URL IP (192.168.50.148) for LAN enrollment
  - NODE_IMAGE env var support in main.py compose generator (configurable from .env)

affects:
  - 06-remote-validation/02c

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Server cert SAN: extract AGENT_URL host at cert generation time, add to SAN list"
    - "Installer CA extraction: jq -> python3 -> grep fallback chain"
    - "Container recreation (not just restart) required to force cert regeneration"

key-files:
  created: []
  modified:
    - puppeteer/agent_service/main.py
    - puppeteer/installer/install_universal.sh
    - puppeteer/compose.server.yaml

key-decisions:
  - "NODE_IMAGE in .env + compose.server.yaml env block: same pattern as AGENT_URL — allows LXC-accessible image reference without hardcoding IP in source"
  - "python3 as CA extraction fallback: available on all Ubuntu nodes, parses JSON correctly (jq grep fallback was broken due to space after colon in token JSON)"
  - "AGENT_URL IP in server cert SAN: read at cert generation, not hardcoded — cert is regenerated on fresh container, persists in writable layer after that"
  - "require_permission() moved above route definitions: was a NameError at startup when new alert/webhook/trigger routes were added at top of file"

patterns-established:
  - "Move all auth helpers (require_permission, get_current_user, etc.) before the first route that uses them"
  - "Token re-enrollment: delete /root/secrets inside LXC node container, then re-run installer with fresh token"

requirements-completed: [REM-03, REM-03a, REM-03b, REM-03d, REM-03f]

# Metrics
duration: 35min
completed: 2026-03-07
---

# Phase 06 Plan 02b: Happy Path Installer Test Summary

**LXC-provisioned Ubuntu 24.04 node fully enrolls via install_universal.sh: CA installed to system trust, secure curl (no -k fallback), heartbeat confirmed in GET /nodes within 5 seconds**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-03-07T14:10:00Z
- **Completed:** 2026-03-07T14:49:00Z
- **Tasks:** 2
- **Files modified:** 3 (main.py, install_universal.sh, compose.server.yaml)

## Accomplishments

- Fixed `main.py` compose template to use `NODE_IMAGE` env var (`192.168.50.148:5000/puppet-node:latest`) — LXC containers can now pull the image
- Fixed `install_universal.sh` to use python3 as CA extraction fallback — token parsing no longer fails when jq is absent
- Fixed server cert SAN generation to include the `AGENT_URL` IP — nodes connecting via LAN IP can now pass SSL verification
- Confirmed full happy path: installer exits 0, CA installed to `/usr/local/share/ca-certificates/mop-root.crt`, node-823aafbd enrolled and appeared in `/nodes` within 5 seconds

## Test Results

| Test | Result | Detail |
|------|--------|--------|
| REM-03a: installer exit code 0 | PASS | exit code 0 |
| REM-03b: CA cert installed | PASS | /usr/local/share/ca-certificates/mop-root.crt found |
| REM-03d: heartbeat within 120s | PASS | node-823aafbd appeared within ~5s |
| REM-03f: no timeout | PASS | completed in <90s (well within 180s) |

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix compose image reference and auth startup ordering** - `b9b5361` (feat)
2. **Task 2: Fix installer CA extraction and server cert SAN** - `0ce9f50` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `puppeteer/agent_service/main.py` — NODE_IMAGE env var in compose generator; require_permission moved above routes; WebhookService/TriggerCreate imports added; AGENT_URL IP added to server cert SAN generation
- `puppeteer/installer/install_universal.sh` — Added python3 as CA extraction fallback between jq and grep
- `puppeteer/compose.server.yaml` — Added NODE_IMAGE env var to agent service environment block

## Decisions Made

- `NODE_IMAGE` uses the same env-var-in-compose pattern as `AGENT_URL`: both `.env` and `compose.server.yaml` environment block required, otherwise docker compose doesn't propagate the value to the container.
- `python3` fallback for CA extraction: the jq grep fallback used `"ca":"..."` but the token JSON has `"ca": "..."` (space after colon). Python's `json.load()` handles both formats correctly and is available on all Ubuntu 24.04 nodes.
- Server cert SAN: `AGENT_URL` is read at cert generation time. The cert is only generated when no existing cert is found (`secrets/cert.pem` absent). Container must be fully recreated (not just restarted) to force cert regeneration.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] require_permission() NameError at startup**
- **Found during:** Task 1 (rebuilding agent image)
- **Issue:** New alert/webhook/trigger routes added by prior sprints were placed at line ~211 in main.py, but `require_permission()` is defined at line 698. Python evaluates `Depends(require_permission(...))` at module load, causing `NameError: name 'require_permission' is not defined` and container crash loop.
- **Fix:** Moved the entire auth helper block (_SPUserProxy, _authenticate_api_key, _authenticate_sp_jwt, get_current_user, get_current_user_optional, _perm_cache, _invalidate_perm_cache, require_permission) from after the installer route handlers to before the first route at line 210.
- **Files modified:** puppeteer/agent_service/main.py
- **Verification:** Container starts cleanly; uvicorn reports "Application startup complete"
- **Committed in:** b9b5361 (Task 1)

**2. [Rule 2 - Missing] Missing imports for WebhookService, WebhookCreate/Response, TriggerCreate/Response**
- **Found during:** Task 1 (rebuilding agent image)
- **Issue:** Routes added in prior sprints referenced WebhookService, WebhookCreate, WebhookResponse, TriggerCreate, and TriggerResponse — none of which were imported in main.py. Container failed to start.
- **Fix:** Added `from .services.webhook_service import WebhookService` and added the missing model names to the existing `from .models import (...)` block.
- **Files modified:** puppeteer/agent_service/main.py
- **Verification:** Import error resolved; server starts
- **Committed in:** b9b5361 (Task 1)

**3. [Rule 1 - Bug] DB schema missing columns for new models**
- **Found during:** Task 1 (after import fixes, server failed at startup DB query)
- **Issue:** Several columns added to DB models in prior sprints were absent from the live PostgreSQL DB. Affected: `capability_matrix.artifact_id`, `scheduled_jobs.max_retries/backoff_multiplier/timeout_minutes`, `jobs.max_retries/retry_count/retry_after/backoff_multiplier/timeout_minutes/depends_on`, `nodes.base_os_family/operator_tags/expected_capabilities/tamper_details/pending_upgrade/upgrade_history`, `tokens.template_id`.
- **Fix:** Applied ALTER TABLE statements directly to the live DB via `docker exec puppeteer-db-1 psql`. Changes not committed as code (no Alembic), logged here for deployment documentation.
- **Files modified:** None (DB-only migration)
- **Verification:** Server starts cleanly; `\d` output confirms all columns present
- **Committed in:** b9b5361 (Task 1 — no code change, but migration is noted in this SUMMARY)

**4. [Rule 1 - Bug] Installer CA extraction fails without jq**
- **Found during:** Task 2 (running installer in LXC — Ubuntu 24.04 doesn't include jq by default)
- **Issue:** The grep fallback `grep -o '"ca":"[^"]*"'` didn't match because the token JSON uses `"ca": "..."` (space after colon). CA extraction returned empty string, installer exited 1.
- **Fix:** Added `elif command -v python3 &>/dev/null` branch using `python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ca',''))"`. Python is available on all Ubuntu 24.04 systems. Also fixed the grep fallback regex to handle optional space: `'"ca": *"[^"]*"'`.
- **Files modified:** puppeteer/installer/install_universal.sh
- **Verification:** Installer exits 0 after fix; CA file created at bootstrap_ca.crt
- **Committed in:** 0ce9f50 (Task 2)

**5. [Rule 1 - Bug] Server cert SAN missing LAN IP — node SSL verification fails**
- **Found during:** Task 2 (puppet-node container logs show SSL mismatch for 192.168.50.148)
- **Issue:** The server cert is generated with SANs from `socket.gethostname()` (resolves to Docker internal IP 172.18.0.7) plus hard-coded hostnames. `192.168.50.148` (LAN IP used by AGENT_URL) was not in the SAN, so nodes connecting via LAN IP failed `certificate verify failed: IP address mismatch`.
- **Fix:** In the cert generation code, parse `AGENT_URL` (already an env var passed to the container) with a regex to extract the host/IP component, then append to `sans` if not already present. The cert is regenerated only on fresh container creation.
- **Files modified:** puppeteer/agent_service/main.py
- **Verification:** Rebuilt container shows "Adding AGENT_URL host to SAN: 192.168.50.148" in logs; `openssl x509 -noout -text` confirms `IP Address:192.168.50.148` in SAN; secure curl succeeds in installer run
- **Committed in:** 0ce9f50 (Task 2)

---

**Total deviations:** 5 auto-fixed (Rules 1, 2, 1, 1, 1)
**Impact on plan:** All fixes were necessary for correctness. The `require_permission` ordering issue and missing imports were pre-existing structural bugs introduced by prior sprints that only manifested when rebuilding the container from updated source. The DB schema gaps and installer CA extraction bug directly blocked the primary objective. No scope creep.

## Issues Encountered

- The `manage_node.py` script fails when running complex shell pipelines via `incus exec mop-test-node -- grep ... || echo ...` because the `||` is evaluated on the host, not inside the container. The script's `test_installer_lxc.py` harness correctly wraps commands in `bash -c '{json.dumps(cmd)}'`, but `manage_node.py` does not. This caused a partial provisioning failure — the container was still usable since all subsequent steps were run directly via `incus exec ... bash -c`. Noted for 06-02c: the test harness handles this correctly.

## Findings for 06-02c (Edge Cases)

- **jq fallback needed:** Ubuntu 24.04 LXC containers don't have jq by default. The python3 fallback now covers this. Wave 3 should test the explicit jq-absent path to confirm.
- **SAN coverage:** The server cert SAN generation is now configurable via AGENT_URL. If operators set a hostname instead of an IP in AGENT_URL, the hostname will be added to the SAN. DNS resolution inside the LXC container should be tested.
- **Insecure curl fallback:** After the CA fix, secure curl succeeded (no fallback). The fallback path (`curl -k`) is still in the installer for scenarios where CA installation fails. Wave 3 should test the fallback path explicitly.
- **manage_node.py sudo line:** The sudoers config step fails when run via `manage_node.py`'s plain `incus exec`. The `test_installer_lxc.py` harness should call `manage_node.py` for provisioning, then handle setup failures gracefully (or use its own `exec_in_container()` for post-setup steps).

## Next Phase Readiness

- Happy path is fully validated — `install_universal.sh` works on fresh Ubuntu 24.04 LXC
- All 4 REM-03 assertions pass
- Server is ready for 06-02c edge-case tests (jq fallback, repeated install, error paths)
- The server cert SAN fix is a permanent improvement — no further action needed for this

---
*Phase: 06-remote-validation*
*Completed: 2026-03-07*
