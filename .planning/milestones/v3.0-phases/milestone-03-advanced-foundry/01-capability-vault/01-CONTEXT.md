# Phase 1: Dynamic Matrix & Artifact Vault - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 focus is the **Persistence** and **Management** layer for capabilities and artifacts. It creates the "Vault" where binaries live and the "Registry" where recipes are defined.

**In Scope:**
- Database schema for Artifacts and Approved OS bases.
- File upload/download logic for binary artifacts.
- API endpoints for Capability Matrix CRUD.
- Admin UI for managing these entities.

**Out of Scope:**
- Heartbeat delivery of upgrades (Phase 3).
- Tamper detection logic (Phase 2).
- Automatic node remediation.

</domain>

<decisions>
## Implementation Decisions

### Artifact Storage
- **Location**: `/app/vault/` inside the orchestrator container.
- **Naming**: Files stored by UUID to prevent collisions; original filename stored in DB.
- **Integrity**: SHA256 hashes generated on upload and verified before serving.

### Capability Matrix
- **Linking**: Added `artifact_id` as a foreign key to the `capability_matrix` table.
- **Macro Expansion**: Support a simple templating syntax in recipes (e.g., `{{ARTIFACT_URL}}`) that the orchestrator expands when serving recipes to Puppets.

### Permissions
- **foundry:write**: Required for modifying the Capability Matrix and uploading artifacts.
- **foundry:read**: Required for listing capabilities and downloading artifacts.

</decisions>

<specifics>
## Specific Ideas

- Add a "Test Download" button in the Artifact UI to verify file integrity.
- Use `StreamingResponse` in FastAPI for large artifact downloads to keep memory usage low.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CapabilityMatrix` model in `db.py`.
- `authenticatedFetch` in dashboard.
- `require_permission` dependency in `main.py`.

### Integration Points
- `puppeteer/agent_service/db.py`: Schema additions.
- `puppeteer/agent_service/main.py`: New API routes.
- `puppeteer/agent_service/services/vault_service.py`: New service for file management.
- `puppeteer/dashboard/src/views/Admin.tsx`: Extend with "Artifacts" and "Matrix" tabs.

</code_context>

---

*Phase: 01-capability-vault*
*Context gathered: 2026-03-05*
