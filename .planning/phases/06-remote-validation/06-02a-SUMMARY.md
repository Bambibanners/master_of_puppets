---
phase: 06-remote-validation
plan: 02a
subsystem: infra
tags: [incus, lxc, podman, docker-registry, installer, testing]

# Dependency graph
requires:
  - phase: 06-remote-validation/01
    provides: Deploy scripts and CA unification for remote nodes

provides:
  - AGENT_URL env var propagation in compose.server.yaml agent service
  - puppet-node image pushed to local registry at localhost:5000/puppet-node:latest
  - LXC installer test harness at mop_validation/scripts/test_installer_lxc.py

affects:
  - 06-remote-validation/02b
  - 06-remote-validation/02c

# Tech tracking
tech-stack:
  added: [incus (LXC), podman-compose (in LXC), docker local registry]
  patterns: [ephemeral LXC container for installer validation, insecure local registry for image pull inside LXC]

key-files:
  created:
    - mop_validation/scripts/test_installer_lxc.py
  modified:
    - puppeteer/compose.server.yaml
    - puppeteer/.env (gitignored — AGENT_URL added)

key-decisions:
  - "AGENT_URL must be added to the agent service environment in compose.server.yaml, not just puppeteer/.env, because docker compose substitutes env vars into compose file expressions"
  - "LXC containers cannot pull from localhost/ image prefix on host — image must be pushed to localhost:5000 registry which is reachable via host bridge IP 192.168.50.148:5000"
  - "Test harness uses --dry-run flag for syntax/config validation without spinning up LXC infrastructure"

patterns-established:
  - "try/finally teardown: always delete LXC container even if tests fail"
  - "Insecure registry config via /etc/containers/registries.conf.d/ inside LXC"
  - "write_file_in_container: push via tempfile rather than shell heredoc for reliability"

requirements-completed: [REM-03, REM-03a, REM-03b, REM-03c, REM-03d, REM-03e, REM-03f]

# Metrics
duration: 5min
completed: 2026-03-07
---

# Phase 06 Plan 02a: LXC Installer Prerequisites Summary

**AGENT_URL propagation fixed in compose.server.yaml, puppet-node image pushed to local registry (localhost:5000), and LXC installer test harness written with 4 assertions and try/finally teardown**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-07T14:04:54Z
- **Completed:** 2026-03-07T14:09:06Z
- **Tasks:** 2
- **Files modified:** 3 (compose.server.yaml, puppeteer/.env, mop_validation/scripts/test_installer_lxc.py)

## Accomplishments

- Added `AGENT_URL=${AGENT_URL:-https://localhost:8001}` to the agent service environment block in `compose.server.yaml` so the LAN IP from `.env` flows into the running container
- Pushed `localhost/master-of-puppets-node:latest` to the local registry as `localhost:5000/puppet-node:latest` — verified via `curl http://localhost:5000/v2/puppet-node/tags/list`
- Wrote `test_installer_lxc.py` with all 11 required steps: provisioning, podman-compose install, registry conf, installer run, 4 assertions (REM-03a/b/d/f), result table, and guaranteed teardown

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix AGENT_URL and push node image to local registry** - `22c961c` (feat) — main repo
2. **Task 2: Write LXC installer test harness** - `54eae3b` (feat) — mop_validation repo

## Files Created/Modified

- `puppeteer/compose.server.yaml` — Added `AGENT_URL` env var to agent service environment block
- `puppeteer/.env` (gitignored) — Added `AGENT_URL=https://192.168.50.148:8001`
- `mop_validation/scripts/test_installer_lxc.py` — Full LXC test harness (442 lines)

## Decisions Made

- `AGENT_URL` needed in compose.server.yaml agent environment block: The agent container ignores env files for variables not listed in the `environment:` section. Adding `${AGENT_URL:-https://localhost:8001}` allows the `.env` value to flow through.
- LXC containers need the image in a registry accessible via the host bridge IP: `localhost/` prefix is not reachable inside LXC, so `localhost:5000/puppet-node:latest` (via `192.168.50.148:5000`) is the correct target.
- Test harness detects the node-compose.yaml image reference and prints a clear diagnosis if it references `localhost/` instead of a registry accessible from LXC.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] AGENT_URL not in compose.server.yaml agent service environment**
- **Found during:** Task 1 (Fix AGENT_URL)
- **Issue:** `puppeteer/.env` had no effect because the agent service `environment:` block in `compose.server.yaml` did not include `AGENT_URL`. `docker exec printenv AGENT_URL` returned nothing after restarting with only the `.env` change.
- **Fix:** Added `- AGENT_URL=${AGENT_URL:-https://localhost:8001}` to the agent service `environment:` section in `compose.server.yaml`. The container was then recreated and the env var confirmed via `docker exec`.
- **Files modified:** `puppeteer/compose.server.yaml`
- **Verification:** `docker exec puppeteer-agent-1 printenv AGENT_URL` returns `https://192.168.50.148:8001`
- **Committed in:** `22c961c` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Fix was necessary for the primary objective — without it, AGENT_URL would never propagate to the agent service regardless of what's in `.env`.

## Issues Encountered

None beyond the deviation above.

## Next Phase Readiness

- Registry is populated with `puppet-node:latest` — LXC containers can pull via `192.168.50.148:5000`
- AGENT_URL is live in the running agent — generated `node-compose.yaml` will use LAN IP for enrollment
- Test harness is ready for plan 02b/02c to run actual installer validation
- Known limitation: `main.py` still generates `node-compose.yaml` with `localhost/master-of-puppets-node:latest` as the image — this will fail inside LXC. Plan 02b should fix the image reference to use `192.168.50.148:5000/puppet-node:latest`.

---
*Phase: 06-remote-validation*
*Completed: 2026-03-07*
