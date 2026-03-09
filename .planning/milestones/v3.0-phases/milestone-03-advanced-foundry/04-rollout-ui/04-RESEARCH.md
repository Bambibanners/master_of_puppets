# Phase 4: Admin Rollout UI & Warning Gates - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 4 provides the operational interface for the hot-upgrade system. It surfaces the security and configuration state of the node runtimes through drift visualization and provides a safe, gated path for administrators to push runtime mutations to Puppets.

## UI Components Analysis

### 1. Capability Drift Visualization
- **Definition**: A node is "drifted" if its `reported_capabilities` do not match its `expected_capabilities`.
- **Implementation**: In `NodeCard.tsx`, we will implement a diffing engine:
    - **Missing Authorized Tool**: Tool exists in `Expected` but not in `Reported`. Highlight as "Pending Install".
    - **Version Mismatch**: Tool versions differ. Highlight as "Update Available".
    - **Unauthorized Tool**: Tool exists in `Reported` but not in `Expected`. This is `TAMPERED` (already implemented in Phase 2).
- **UX**: A new "Runtime Health" section in the card, showing a list of tools with status icons.

### 2. Hot-Upgrade Workflow (Per-Node)
- **Action**: Add an "Apply Upgrade" button to the `NodeCard` (visible to admins).
- **Selection**: Opens a `HotUpgradeModal` showing available recipes from the `CapabilityMatrix` filtered by the node's `base_os_family`.
- **Safety Gate**: A multi-step confirmation:
    1. Warning text about runtime mutation.
    2. Review of the specific `injection_recipe`.
    3. Mandatory "Type 'UPGRADE' to confirm" input.

### 3. Centralized Rollout Tool
- **Goal**: Allow pushing a tool to multiple nodes at once (staged rollout).
- **Location**: A new "Rollouts" tab in the `Admin.tsx` view.
- **Workflow**:
    1. Select Tool from Matrix.
    2. Filter/Select Nodes (by status, env tag, or manual selection).
    3. Preview the impact.
    4. Batch execute the `/api/nodes/{id}/upgrade` calls.

## Requirement Analysis
- **TAG-01**: Admin-controlled upgrades. (Handled by Per-node UI).
- **TAG-02**: Staged rollouts. (Handled by Rollout Tab).
- **TAG-03**: Safety gates. (Handled by Modal confirmation).

## Technical Strategy
1. **Refactor `NodeCard.tsx`**: Add the drift visualization logic and the per-node upgrade button.
2. **Create `HotUpgradeModal.tsx`**: A reusable modal for staging upgrades with the required safety gates.
3. **Extend `Admin.tsx`**: Add the "Rollouts" tab for bulk operations.

## Potential Pitfalls
- **UI Clutter**: `NodeCard` is already dense. Use collapsible sections or a "Manage Runtime" drill-down.
- **Async Feedback**: The upgrade process takes time (30s heartbeat + install time). The UI must show "Staged" or "Upgrading..." status clearly to prevent redundant requests.

---
*Phase: 04-rollout-ui*
*Context: Master of Puppets Advanced Foundry Milestone*
