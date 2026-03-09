---
gsd_state_version: 1.0
milestone: milestone-7
milestone_name: Advanced Foundry & Smelter
status: planning
stopped_at: Milestone 7 started — defining requirements
last_updated: "2026-03-09T00:00:00.000Z"
last_activity: "2026-03-09 — Milestone 7 kickoff: Advanced Foundry & Smelter"
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-09)

**Core value:** Jobs run reliably — on the right node, when scheduled, with output captured — without weakening the security model.
**Current focus:** Milestone 7 — Advanced Foundry & Smelter (requirements phase)

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements for Milestone 7 — Advanced Foundry & Smelter
Last activity: 2026-03-09 — Milestone 7 started

Progress: [░░░░░░░░░░] 0% (0 of 0 phases complete)

## Performance Metrics

**Velocity:**
- Phase 7 (07-linux-installer), Plan 02a: 5 min, 2 tasks, 3 files

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 06-remote-server | 2 | 5 min | 2.5 min |
| Phase 07-linux-installer P02b | 35 | 2 tasks | 3 files |
| Phase 07-linux-installer P02c | 39 | 2 tasks | 2 files |
| Phase 08-cross-network-validation P01 | 10 | 2 tasks | 1 files |
| Phase 08-cross-network-validation P02 | 150 | 2 tasks | 3 files |
| Phase 09-triggermanager-dashboard-ui P01 | 2 | 2 tasks | 4 files |
| Phase 09 P02 | 2 | 2 tasks | 1 files |
| Phase 09-triggermanager-dashboard-ui P03 | 5 | 2 tasks | 0 files |
| Phase 10-windows-installer-fix P01 | 2 | 2 tasks | 2 files |
| Phase 10 P02 | 2 | 2 tasks | 2 files |

## Accumulated Context

### Decisions
- Milestone 4: Focus on "Headless" operation and machine-to-machine integrations.
- Milestone 4: Implement dedicated trigger endpoints for CI/CD systems.
- Phase 06-02a: AGENT_URL must be in compose.server.yaml agent environment block (not just .env) for docker compose to pass it through.
- Phase 06-02a: LXC containers need image in localhost:5000 registry (host bridge accessible) — cannot pull from localhost/ prefix.
- Phase 06-02a: node-compose.yaml still references localhost/ image — plan 02b should fix this in main.py.
- [Phase 06-remote-validation]: NODE_IMAGE env var in compose template (main.py) + compose.server.yaml env block enables configurable node image for LXC/remote deployments
- [Phase 06-remote-validation]: Server cert SAN now includes AGENT_URL IP via parsing at cert generation time — allows remote nodes to verify server identity by LAN IP
- [Phase 06-remote-validation]: install_universal.sh: python3 is the preferred CA extraction fallback over grep — available on all Ubuntu systems and handles any JSON spacing
- [Phase 06-remote-validation]: printf '%s' over echo for JSON variables: bash echo interprets \n as newlines, corrupting JSON passed to jq/python3/grep — printf '%s' preserves literal backslash-n sequences
- [Phase 06-remote-validation]: Non-root heartbeat not required as test pass criterion — rootless podman + LXC cgroupv2 is an infrastructure constraint, not an installer defect
- [Phase 08-cross-network-validation]: server_url as explicit first parameter on all API helpers (not a global) so Docker and Podman stacks can be tested against different server IPs in one script run
- [Phase 08-cross-network-validation]: No default container in exec_in_container/push_file prevents accidental cross-container execution when provisioning two stacks simultaneously
- [Phase 08-cross-network-validation]: run_stack_tests() returns skip() stubs so script runs cleanly before Plans 02/03 implement real assertions
- [Phase 08-cross-network-validation]: NODE_EXECUTION_MODE=direct required for DinD cross-network nodes — no Docker socket mounted inside node containers running inside LXC-hosted Docker
- [Phase 08-cross-network-validation]: Both signing.key and verification.key must be written to build context before compose --build to prevent pki.py ensure_signing_key() from regenerating keypair at server startup
- [Phase 08-cross-network-validation]: Server returns naive UTC datetimes (no tz suffix) — must call ts.replace(tzinfo=utc) when comparing to timezone-aware datetimes
- [Phase 08-cross-network-validation]: Server has no GET /jobs/{guid} endpoint; poll using GET /jobs list and filter by guid; job output in GET /jobs/{guid}/executions
- [Phase 09-triggermanager-dashboard-ui]: PATCH and regenerate-token both use foundry:write permission gate - consistent with existing trigger routes
- [Phase 09]: Copy Token uses navigator.clipboard directly with no confirmation dialog for immediate UX
- [Phase 09]: Enable trigger sends PATCH immediately; only Disable requires AlertDialog confirmation
- [Phase 09-triggermanager-dashboard-ui]: All 9 TriggerManager verification steps passed in browser — feature confirmed working end-to-end
- [Phase 10-windows-installer-fix]: Inline function stubs in BeforeEach (not dot-source) for Wave 0 — target functions don't exist in ps1 yet; dot-source added in Plan 02
- [Phase 10-windows-installer-fix]: Fedora 40 base for loader/Containerfile — ships podman in default repos without multi-step manual install
- [Phase 10]: TCP relay cleanup uses finally block to ensure relay Start-Job is stopped even if podman loader throws
- [Phase 10]: Get-PodmanSocketInfo defined but not called in Method-1 — placeholder for future named pipe mounting; current approach uses DOCKER_HOST TCP relay
- [Phase 10-windows-installer-fix]: WIN-05 Pester assertion narrowed to 'Get-Command podman-compose' — functional check only, not raw string match which falsely triggered on menu description text
- [Phase 10-windows-installer-fix]: WIN-06/WIN-07 deferred — no local Podman or Windows/WSL2 hardware; phase closed with WIN-01..05 automated green gate; retest when hardware available
- [Phase 10-windows-installer-fix]: WIN-06/WIN-07 deferred — no local Podman or Windows/WSL2 hardware; phase closed with WIN-01..05 automated green gate; retest when hardware available

### Pending Todos
- Plan 02b: Fix node-compose.yaml image reference in main.py (localhost/ → 192.168.50.148:5000/).
- Run test_installer_lxc.py and fix any installer issues found.

### Blockers/Concerns
- node-compose.yaml generated by main.py still uses `localhost/master-of-puppets-node:latest` which is unreachable from inside LXC — next plan must fix this.

## Session Continuity

Last session: 2026-03-09
Stopped at: Milestone 7 kickoff — research in progress
Resume file: None
Next plan: Complete requirements definition → spawn roadmapper → /gsd:plan-phase 11
