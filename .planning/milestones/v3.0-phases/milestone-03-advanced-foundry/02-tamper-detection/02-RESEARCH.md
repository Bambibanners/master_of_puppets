# Phase 2: Capability Expectation & Tamper Detection - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 2 implements the "Zero-Trust Capability" model. Instead of the orchestrator blindly accepting what a node claims it can do, the orchestrator now maintains an "Authorized" list of capabilities (`expected_capabilities`). Any deviation where a node reports *more* than it was granted is treated as a security breach (tampering).

## Core Concepts

### 1. Authorized Capabilities
- A node's authorized capabilities are derived from the `PuppetTemplate` it was provisioned with.
- A `PuppetTemplate` links to a `Blueprint`, which defines the tools (e.g., `python-3.11`, `powershell-7.4`).
- These tools form the `expected_capabilities` map for the node.

### 2. Tamper Detection Logic
- Triggered during the Heartbeat process.
- **Detection Rule**: If `reported_capabilities` contains any key (tool_id) that is NOT present in `expected_capabilities`, the node is flagged.
- **Status Change**: The node status transitions to `TAMPERED`.
- **Quarantine**: Nodes in `TAMPERED` status are ineligible for job assignment in `JobService.pull_work`.

### 3. Lifecycle of Expectations
- **Initialization**: Set during `enroll_node`. The enrollment token must now optionally carry a `template_id`.
- **Updates**: When an admin triggers a "Hot-Upgrade" (Phase 3), the `expected_capabilities` are updated *after* the upgrade is verified.
- **Recovery**: Only an administrator can clear a `TAMPERED` flag via the dashboard/API.

## Technical Requirements

### Database Changes
- **Table `nodes`**:
    - `expected_capabilities`: `Text` (JSON).
    - `tamper_details`: `Text` (Optional description of the breach).
- **Table `tokens`**:
    - `template_id`: `String` (Link to `PuppetTemplate`).

### API Changes
- `POST /admin/generate-token`: Accept `template_id`.
- `POST /api/nodes/{node_id}/clear-tamper`: Admin-only endpoint to restore node status.
- `GET /api/nodes`: Include `expected_capabilities` and tamper status in `NodeResponse`.

### Service Changes
- `JobService.receive_heartbeat`: Implement the comparison logic.
- `JobService.pull_work`: Add a guard clause against `TAMPERED` nodes.

## Potential Pitfalls
- **Legacy Nodes**: Nodes enrolled before this phase won't have `expected_capabilities`. 
    - *Decision*: If `expected_capabilities` is null, skip tamper detection (Permissive mode) or require a manual "Sync" by an admin.
- **Version Noise**: Minor version variations (e.g., `3.11.4` vs `3.11.5`) might trigger false positives if not handled via semantic versioning ranges.
    - *Decision*: Focus on `tool_id` presence first. Version-level tampering can be added as a refinement.

---
*Phase: 02-tamper-detection*
*Context: Master of Puppets Advanced Foundry Milestone*
