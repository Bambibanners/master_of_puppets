# Phase 4: Provisioning & UI Parity - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 4 focuses on bridging the final gaps in the dashboard user experience, specifically regarding node provisioning, network mount management, and build feedback visibility.

## Current Implementation Analysis
- **Node Provisioning**: `AddNodeModal` is wired in `Nodes.tsx`, but its functionality needs to be verified end-to-end.
- **Network Mounts**:
    - **Backend**: `GET /config/mounts` and `POST /config/mounts` are fully implemented.
    - **Frontend**: The "Network Mounts" button is wired to `showMountsModal`, but the `ManageMountsModal` component does not exist, causing potential build/runtime errors.
- **Build Feedback**: `Templates.tsx` triggers image builds but only shows a generic "Building..." or "Build succeeded/failed" message. The user cannot see the actual output of the build command.
- **Node Stats**: `Nodes.tsx` correctly uses `node.stats_history` (from `list_nodes` backend), so mock data is no longer being used.

## Gap Analysis
1.  **Missing Component**: `ManageMountsModal.tsx` needs to be created to allow operators to manage global SMB/NFS mounts.
2.  **Build Visibility**: Operators need a way to view the output of `podman/docker build` when a template build fails (or succeeds).
3.  **UI Polish**: Ensure `AddNodeModal` correctly handles the new `-Tags` parameter implemented in Milestone 1 Phase 4.

## Technical Strategy
1.  **Create `ManageMountsModal.tsx`**: Implementation should include a dynamic form for adding/removing mount definitions (name, path, options).
2.  **Enhance `Templates.tsx`**: Add a "View Build Logs" button that opens a modal showing the `status` field from the `ImageResponse` (which now contains the last 200 chars of build output).

---
*Phase: 04-provisioning-ui*
*Context: Master of Puppets Milestone 2*
