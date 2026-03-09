# Phase 3: Hot-Upgrade Engine - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 implements the **Execution** layer of the Hot-Upgrade system. It enables the actual mutation of node runtimes by bridging the orchestrator's capability registry with the node's local environment via the heartbeat C2 loop.

**In Scope:**
- Orchestrator: Schema for `pending_upgrade` and `upgrade_history`.
- Orchestrator: API to stage upgrades.
- Orchestrator: Heartbeat response enhancement.
- Node: Logic to receive, execute, and report upgrades.
- Security: Recipe signature verification.

**Out of Scope:**
- Staged rollouts/Canary releases (Phase 4).
- Bulk upgrades (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### Communication Channel
- **Heartbeat Response**: The upgrade payload will be delivered as part of the standard 30s heartbeat response.
- **Why**: Avoids opening new ports on the node and leverages existing authenticated/mTLS traffic.

### Execution Isolation
- **Subprocess**: Recipes will be executed as shell subprocesses.
- **Quarantine**: While upgrading, the node will report a status of `UPGRADING` and the orchestrator will set its `concurrency_limit` to 0.

### Trust Model
- **Signed Recipes**: To prevent Man-in-the-Middle or server-side compromise from executing arbitrary shell commands, all recipes will be signed using the orchestrator's master Ed25519 key. The node will verify the signature before execution.

### Promotion
- **Atomic Promotion**: The `expected_capabilities` map is only updated on the orchestrator AFTER the node reports a successful `validation_cmd` execution.

</decisions>

<specifics>
## Specific Ideas

- Store the last 10 upgrade attempts in `Node.upgrade_history` for auditability.
- If an artifact is required, use `httpx` on the node to download it from the Artifact Vault using the node's existing client certificate.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SignatureService` for Ed25519 signing.
- `VaultService` for artifact URL generation.
- `subprocess.run` wrappers in `node.py`.

### Integration Points
- `puppeteer/agent_service/db.py`: `Node` model updates.
- `puppeteer/agent_service/services/job_service.py`: `receive_heartbeat` logic.
- `puppeteer/agent_service/main.py`: Upgrade staging API.
- `puppets/environment_service/node.py`: Heartbeat loop and execution engine.

</code_context>

---

*Phase: 03-hot-upgrade-engine*
*Context gathered: 2026-03-05*
