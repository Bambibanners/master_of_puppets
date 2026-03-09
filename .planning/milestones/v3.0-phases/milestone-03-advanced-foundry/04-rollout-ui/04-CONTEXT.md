# Phase 4: Admin Rollout UI & Warning Gates - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 is the **Visual Management** layer. It makes the hot-upgrade engine accessible to operators and enforces the requested safety gates for production state changes.

**In Scope:**
- UI for comparing Reported vs Authorized capabilities.
- Per-node "Apply Upgrade" workflow with multi-step confirmation.
- Admin Rollout dashboard for batch upgrades.
- Real-time progress tracking for staged upgrades.

**Out of Scope:**
- Automatic remediation (automatic self-healing).
- Historical diffing (viewing what a node had 1 week ago).

</domain>

<decisions>
## Implementation Decisions

### Drift Detection UI
- **Logic**: Client-side comparison of `node.capabilities` vs `node.expected_capabilities`.
- **States**:
    - **In Compliance**: (Green) All expected tools are present and versioned.
    - **Drifted**: (Amber) Expected tools missing or outdated.
    - **Tampered**: (Red) Reported tools not in authorized list (implemented in Phase 2).

### Multi-step Confirmation (Gates)
- **Step 1**: Summary of what will change.
- **Step 2**: Technical preview of the bash script (Injection Recipe).
- **Step 3**: Destructive action confirmation (Type 'UPGRADE').

### Rollout Orchestration
- Simple bulk implementation: The frontend will iterate over selected nodes and fire the `/upgrade` API for each.
- Provides a summary of "Staged / Pending" after the bulk action.

</decisions>

<specifics>
## Specific Ideas

- Add a "Runtime Details" expander to the `NodeCard` to keep the default view clean.
- Use a "Pulse" animation for nodes in the `UPGRADING` state.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CapabilityMatrixManager` query.
- `AlertDialog` components.
- `Badge` component styles.

### Integration Points
- `puppeteer/dashboard/src/views/Nodes.tsx`: Node status and drift logic.
- `puppeteer/dashboard/src/components/HotUpgradeModal.tsx`: New component for safety gates.
- `puppeteer/dashboard/src/views/Admin.tsx`: Add "Rollouts" tab.

</code_context>

---

*Phase: 04-rollout-ui*
*Context gathered: 2026-03-05*
