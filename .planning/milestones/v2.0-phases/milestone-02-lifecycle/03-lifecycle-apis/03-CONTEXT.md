# Phase 3: Lifecycle & Admin APIs - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 focuses on administrative completeness. It ensures that any entity created by an operator can also be modified or removed, and that the dashboard provides intuitive controls for these lifecycle events.

This phase is purely focused on existing entity types (Blueprints, Templates, Job Definitions, Service Principals).

</domain>

<decisions>
## Implementation Decisions

### Blueprint Deletion
- **Location**: `Templates.tsx` -> `BlueprintItem`.
- **Feedback**: Use standard `sonner` toasts to surface both success and 409 (Conflict) errors when a blueprint is in use.

### Service Principal & Signature Cleanup
- **Requirement**: Verify visibility. If missing, add delete buttons to the respective management tables.

</decisions>

<specifics>
## Specific Ideas

- When a blueprint delete button is clicked, show a native browser `confirm()` dialog first to prevent accidental deletion.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `deleteMutation` pattern in `Templates.tsx`.
- `authenticatedFetch` wrapper.

### Integration Points
- `puppeteer/dashboard/src/views/Templates.tsx`: Primary UI component.
- `puppeteer/dashboard/src/views/Admin.tsx`: Service principal management.
- `puppeteer/dashboard/src/views/Signatures.tsx`: Public key management.

</code_context>

---

*Phase: 03-lifecycle-apis*
*Context gathered: 2026-03-05*
