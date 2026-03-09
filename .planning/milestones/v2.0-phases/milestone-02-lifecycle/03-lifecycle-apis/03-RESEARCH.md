# Phase 3: Lifecycle & Admin APIs - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 3 focuses on ensuring that all platform entities (Blueprints, Templates, and Job Definitions) can be managed throughout their entire lifecycle, including deletion and state toggling. 

## Current Implementation Analysis
- **Job Definitions**: Fully functional. `DELETE` and `/toggle` endpoints exist in the backend and are wired to the `JobDefinitionList` UI.
- **Templates**: Deletion is implemented in both the backend (`DELETE /api/templates/{id}`) and the frontend (`Templates.tsx`).
- **Blueprints**:
    - **Backend**: `DELETE /api/blueprints/{id}` exists and correctly prevents deletion if referenced by a template.
    - **Frontend**: The `BlueprintItem` in `Templates.tsx` is missing a delete button.
- **Service Principals**: `DELETE /admin/service-principals/{sp_id}` exists but needs UI verification.
- **Signatures**: `DELETE /signatures/{id}` exists but needs UI verification.

## Gap Analysis
1.  **Blueprint Management UI**: Add a delete button to the `BlueprintItem` component in `Templates.tsx`.
2.  **Delete Feedback**: Ensure that when a blueprint deletion fails because it's "referenced by a template," the error message is clearly surfaced to the user.
3.  **Entity Cleanup**: Verify if deleting a template should also trigger a cleanup of the built image in the local registry (deferred for now as images are small and re-usable).

## Technical Strategy
1.  **Update `Templates.tsx`**: Implement the `deleteMutation` for blueprints and add the `Trash2` button to `BlueprintItem`.
2.  **Audit UI Coverage**: Quickly check `Admin.tsx` or wherever Service Principals are managed to ensure delete buttons are present.

---
*Phase: 03-lifecycle-apis*
*Context: Master of Puppets Milestone 2*
