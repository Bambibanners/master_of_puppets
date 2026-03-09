# Phase 9: TriggerManager Dashboard UI - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete the Automation Triggers management UI in Admin.tsx. The TriggerManager component and Automation tab are partially written but broken (missing imports for Dialog and Label cause compile errors) and incomplete (no is_active management, no empty state). This phase fixes the compile errors, adds the missing features, and adds a backend PATCH endpoint to support them.

This phase is strictly about the TriggerManager component and the backend endpoints it needs. Other Admin tabs and unrelated features are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Active/inactive toggle
- Add an inline toggle to each table row: green "Active" / grey "Inactive" badge + a toggle button in the Actions column
- Requires adding `PATCH /api/admin/triggers/{id}` backend endpoint to update `is_active`
- Toggling a trigger **inactive** shows a confirmation dialog before sending the PATCH: "Disabling this trigger will prevent new jobs from being fired. Continue?"
- No side effects beyond flipping `is_active` — in-flight jobs complete normally

### Secret token management
- Add a **Copy Token** button in each row (alongside the existing Copy Curl button)
- Add a **Rotate Key** button in the Actions column that opens a confirmation dialog: "This will invalidate the current token. Existing integrations will break until updated."
- After regeneration, display the new token in a **one-time reveal modal** with a Copy button and a warning: "This is the only time you'll see this token." (mirrors the Service Principal key reveal pattern)
- Requires a backend endpoint: `POST /api/admin/triggers/{id}/regenerate-token` (or equivalent PATCH field)

### Empty state
- When no triggers exist, replace the empty table body with a centered message inside the table: "No triggers yet."
- Include a one-line description: "Triggers are secure webhooks that let external systems (GitHub Actions, scripts) fire jobs."
- Include a "+ Create Trigger" button that opens the create dialog
- The Create Trigger button in the card header remains as well

### Compile fixes
- Add missing imports: `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogFooter` from `@/components/ui/dialog`
- Add missing import: `Label` from `@/components/ui/label`

### Claude's Discretion
- Exact icon choice for Rotate Key button
- Styling details for confirmation dialogs (reuse existing modal styling pattern from the file)
- Whether regenerate-token is a separate POST endpoint or a field on the PATCH endpoint
- RBAC: use existing `admin` permission gate (same as create/delete triggers)

</decisions>

<specifics>
## Specific Ideas

- The one-time reveal modal for the new token should mirror the Service Principal key reveal pattern already in the codebase (check ServicePrincipals.tsx for the pattern)
- The confirmation dialog for disabling a trigger can reuse the AlertDialog component if it's available, or a simple Dialog with Cancel/Confirm buttons

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogFooter` from `@/components/ui/dialog` — missing from current imports, need to be added
- `Label` from `@/components/ui/label` — missing from current imports, need to be added
- `authenticatedFetch` — already used in TriggerManager for all API calls
- `useQuery`, `useMutation`, `useQueryClient` from `@tanstack/react-query` — already in use
- `toast` from `sonner` — already in use for success feedback
- `Badge` — already imported, use for Active/Inactive status display
- ServicePrincipals.tsx — has a one-time key reveal pattern to reference for the regenerate-token modal

### Established Patterns
- Table with actions column: already used in TriggerManager and throughout Admin.tsx
- Confirmation-before-destructive-action: consistent pattern in the codebase
- `invalidateQueries` on mutation success: already in use in TriggerManager

### Integration Points
- `puppeteer/dashboard/src/views/Admin.tsx`: TriggerManager component (lines 54–213), Automation tab (line 690)
- `puppeteer/agent_service/services/trigger_service.py`: needs `update_trigger()` and `regenerate_token()` methods
- `puppeteer/agent_service/main.py`: needs PATCH and token-regeneration endpoints added to the Trigger API section (~line 2307)
- `puppeteer/agent_service/models.py`: needs `TriggerUpdate` Pydantic model

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-triggermanager-dashboard-ui*
*Context gathered: 2026-03-08*
