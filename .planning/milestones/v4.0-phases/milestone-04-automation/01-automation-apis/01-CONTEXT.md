# Phase 1: Automation APIs - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 focuses on **Ingress Automation**. It creates the specialized endpoints designed for non-interactive systems (CI/CD, external scripts) to safely and simply trigger workloads on the Puppeteer mesh.

**In Scope:**
- Database schema for `Trigger` definitions.
- Public `/api/trigger/{slug}` endpoint.
- HMAC or simple Token-based authentication for triggers.
- Management UI for creating and managing triggers.

**Out of Scope:**
- Webhook callbacks *from* MOP to external systems (Egress automation).
- Advanced conditional signal logic (Phase 2).

</domain>

<decisions>
## Implementation Decisions

### Trigger slugs
- **Format**: URL-friendly slugs (e.g., `rebuild-cache`, `deploy-frontend`).
- **Persistence**: Stored in a new `triggers` table.

### Security Model
- **Token Isolation**: Each trigger has its own `secret_token`.
- **RBAC**: Creating triggers requires `admin` role. Firing triggers only requires the specific trigger token.
- **Fixed Targets**: Triggers are bound to a specific `ScheduledJob`. The caller can provide data, but they cannot change the script or target tags of the underlying job definition.

### Rate Limiting
- Use the existing `slowapi` limiter on the trigger endpoint to prevent brute-force or runaway pipeline loops.

</decisions>

<specifics>
## Specific Ideas

- Provide a "Copy as curl" button in the Trigger management UI.
- Support JSONPath-like expansion for trigger variables in the job payload.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `JobService.create_job`: The foundation for actually launching the task.
- `ScheduledJob` ORM: The source template for most triggers.
- `slowapi` integration in `main.py`.

### Integration Points
- `puppeteer/agent_service/db.py`: Schema additions.
- `puppeteer/agent_service/main.py`: New API routes.
- `puppeteer/agent_service/services/trigger_service.py`: New business logic layer.
- `puppeteer/dashboard/src/views/Admin.tsx`: New tab for "Automation".

</code_context>

---

*Phase: 01-automation-apis*
*Context gathered: 2026-03-05*
