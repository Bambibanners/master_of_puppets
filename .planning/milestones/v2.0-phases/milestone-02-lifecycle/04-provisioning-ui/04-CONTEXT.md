# Phase 4: Provisioning & UI Parity - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 concludes Milestone 2 by delivering a complete, functional UI for node lifecycle and platform configuration. It bridges the gap between available backend APIs (Mounts, Build Logs) and the user dashboard.

This phase is strictly about UI components and their integration with existing backend endpoints.

</domain>

<decisions>
## Implementation Decisions

### ManageMountsModal
- **Behavior**: Fetch existing mounts on open. Allow adding multiple "Mount" entries (Name, Remote Path). On save, send the entire list to `POST /config/mounts`.
- **Validation**: Ensure paths start with `//` or `/` and names are alphanumeric.

### Build Log Modal
- **Behavior**: When a build fails, the `Templates.tsx` card should show a "View Details" button.
- **Content**: Display the `status` string from the API, which includes the trailing build output.

</decisions>

<specifics>
## Specific Ideas

- The `ManageMountsModal` should use a "List" pattern where rows can be added/removed dynamically before hitting "Save Changes".

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Dialog` and `Input` components from the UI library.
- `authenticatedFetch` for API calls.

### Integration Points
- `puppeteer/dashboard/src/components/ManageMountsModal.tsx`: New file to be created.
- `puppeteer/dashboard/src/views/Nodes.tsx`: Already imports and expects `ManageMountsModal`.
- `puppeteer/dashboard/src/views/Templates.tsx`: Needs "View Details" logic added to the template cards.

</code_context>

---

*Phase: 04-provisioning-ui*
*Context gathered: 2026-03-05*
