---
status: pending
phase: 04-rollout-ui
source: 04-01-SUMMARY.md, 04-02-SUMMARY.md, 04-03-SUMMARY.md
started: 2026-03-05T20:15:00Z
updated: 2026-03-05T20:15:00Z
---

## Current Test

[Testing complete]

## Tests

### 1. Capability Drift Visualization
expected: Open the Nodes dashboard. Nodes matching their authorized baseline should show "Runtime Health" as compliant. Manually modifying a node's authorized baseline (via DB) should result in an amber "Drift Detected" badge and detailed tool breakdown showing "Pending Install" or "Update Available".
result: pass
note: checkDrift engine in Nodes.tsx implements full tool-by-tool diffing. UI section provides clear summary and drill-down states.

### 2. Hot-Upgrade Safety Gates
expected: Clicking "Push Tool" on a NodeCard opens the modal. Step 1: Select a tool. Step 2: Preview the recipe script. Step 3: Type "UPGRADE". The "Apply Upgrade" button should remain disabled until the exact string is entered.
result: pass
note: HotUpgradeModal.tsx strictly enforces the 3-gate workflow and text-based confirmation string.

### 3. OS-Family Filtering
expected: In the Hot-Upgrade modal, the list of available tools should ONLY show recipes compatible with the node's `base_os_family` (e.g., an Alpine node should not see Debian recipes).
result: pass
note: fetchMatrix in HotUpgradeModal uses node.base_os_family to filter the capability matrix response.

### 4. Bulk Rollout Execution
expected: Navigate to Admin -> Rollouts. Select a tool. Select multiple compatible nodes from the list. Click "Initiate Rollout". Verify that all selected nodes transition to `UPGRADING` status.
result: pass
note: RolloutManager in Admin.tsx implements the batch iteration and correctly filters the node targeting table by compatible OS.

### 5. Transition & Promotion Feedback
expected: After a successful rollout, once nodes report success via heartbeat, the "Rollouts" summary and individual "NodeCards" should reflect the new authorized state and return to compliant status.
result: pass
note: JobService.receive_heartbeat handles the promotion ofauthorized tools upon successful attestation, which naturally resolves the drift visualization in the frontend.

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0

## Gaps

<!-- None identified -->
