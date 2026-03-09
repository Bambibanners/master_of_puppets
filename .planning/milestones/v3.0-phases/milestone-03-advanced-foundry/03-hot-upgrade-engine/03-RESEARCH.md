# Phase 3: Hot-Upgrade Engine - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 3 implements the command-and-control (C2) loop for in-place node upgrades. It allows the orchestrator to push "Injection Recipes" (shell scripts) and binaries to deployed Puppets via the existing heartbeat mechanism.

## Hot-Upgrade Flow

### 1. Staging (Orchestrator)
- Admin selects a node and a tool from the Capability Matrix.
- Orchestrator calculates the `upgrade_task`:
    - `tool_id`: The tool being installed (e.g., `python-3.12`).
    - `recipe`: The shell commands to run.
    - `artifact_url`: (Optional) Internal URL to the binary in the Vault.
    - `validation_cmd`: Command to verify success (e.g., `python3 --version`).
- Task is stored in `Node.pending_upgrade`.

### 2. Delivery (Heartbeat)
- Node sends heartbeat.
- `JobService.receive_heartbeat` checks `node.pending_upgrade`.
- If a task is pending, it is included in the JSON response:
  ```json
  {
    "status": "ack",
    "upgrade_task": { "recipe": "...", "artifact_url": "...", "validation_cmd": "..." }
  }
  ```

### 3. Execution (Puppet Agent)
- Node `heartbeat_loop` receives the task.
- Node enters `UPGRADING` state (concurrency = 0).
- Node downloads the artifact (if url present).
- Node executes the `recipe` as a shell subprocess.
- Node runs `validation_cmd`.
- Node captures the output and exit code.

### 4. Attestation & Promotion
- Node reports the outcome in its *next* heartbeat:
  ```json
  {
    "node_id": "...",
    "upgrade_result": { "status": "SUCCESS", "output": "..." }
  }
  ```
- Orchestrator verifies the result.
- On SUCCESS:
    - `expected_capabilities` is updated to include the new tool.
    - `pending_upgrade` is cleared.
    - Node status returns to `ONLINE`.

## Technical Requirements

### Database
- `Node.pending_upgrade`: `Text` (JSON).
- `Node.upgrade_history`: `Text` (JSON list of past transactions).

### Agent (Node)
- Implementation of a `HotUpgradeManager` or similar within `node.py`.
- Ability to run multi-line shell scripts safely.
- Temporary file management for artifact downloads.

### Security
- **Signature Verification**: Upgrade recipes should ideally be signed by the orchestrator (using the same Ed25519 key used for jobs). Nodes must reject unsigned or invalidly signed upgrades.
- **Authorization**: Only `expected_capabilities` is promoted. If a node reports a tool it wasn't staged for, it's still treated as `TAMPERED`.

## Potential Pitfalls
- **Heartbeat Frequency**: 30s heartbeat might be too slow for responsive upgrades. 
    - *Decision*: Keep 30s; this is a background management task, not real-time.
- **Recipe Failures**: Broken recipes could leave the node in a weird state.
    - *Decision*: Validation command is the final source of truth. If it fails, the upgrade fails.
- **Bandwidth**: Downloading large artifacts every heartbeat?
    - *Decision*: Node must only download if the `artifact_id` has changed or if not currently installed.

---
*Phase: 03-hot-upgrade-engine*
*Context: Master of Puppets Advanced Foundry Milestone*
