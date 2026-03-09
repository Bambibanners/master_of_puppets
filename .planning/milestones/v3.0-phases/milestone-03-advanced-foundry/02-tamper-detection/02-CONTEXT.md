# Phase 2: Capability Expectation & Tamper Detection - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 introduces the **Security Guard** for node runtimes. It establishes the "Authorized State" for every Puppet and implements the logic to detect and quarantine nodes that deviate from this state by self-reporting unauthorized tools.

**In Scope:**
- Schema changes for `Node` and `Token` to track authorized capabilities.
- Logic to derive expected capabilities from templates during enrollment.
- Heartbeat comparison logic (Reported vs Expected).
- Node quarantine mechanism (TAMPERED status).
- Admin API to clear tamper alerts.

**Out of Scope:**
- Automatic remediation (Phase 3).
- Fine-grained version tampering (beyond simple tool presence).

</domain>

<decisions>
## Implementation Decisions

### Tamper Rule
- **Primary Rule**: If `Reported` has a key that `Expected` does not -> **TAMPERED**.
- **Secondary Rule**: If `Expected` is missing from `Reported` -> **DRIFTED** (Warning only, not quarantined, as this might be a temporary failure or partial install).

### Quarantine Mechanism
- A node marked as `TAMPERED` is functionally disabled for job execution.
- `JobService.pull_work` will skip these nodes.
- The dashboard should show a critical alert for these nodes.

### Enrollment Link
- The `Token` table will gain a `template_id` field.
- If a node enrolls with a token that has a `template_id`, its `expected_capabilities` are set immediately.
- If no `template_id` is present, `expected_capabilities` remains null, and the node operates in "Legacy/Permissive" mode.

</decisions>

<specifics>
## Specific Ideas

- Log the specific tool that triggered the tamper alert in `tamper_details`.
- Add a "Clear Alert" button in the Node settings modal.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `JobService.receive_heartbeat` logic.
- `enroll_node` endpoint in `main.py`.
- `Token` and `Node` models in `db.py`.

### Integration Points
- `puppeteer/agent_service/db.py`: Model updates.
- `puppeteer/agent_service/services/job_service.py`: Comparison and guard logic.
- `puppeteer/agent_service/main.py`: Admin token and node management endpoints.
- `puppeteer/dashboard/src/views/Nodes.tsx`: UI for tamper alerts.

</code_context>

---

*Phase: 02-tamper-detection*
*Context gathered: 2026-03-05*
