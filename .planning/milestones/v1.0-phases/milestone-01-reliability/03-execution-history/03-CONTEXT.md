# Phase 3: Execution History - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 transitions the system from per-job execution logs to a global, queryable audit timeline. It introduces automated history retention to prevent database bloat and provides a unified view of all node activity across the entire platform.

Phase 1 established the `ExecutionRecord` table and basic capture. Phase 2 (if implemented) handled retries. Phase 3 focuses on the visibility, management, and performance of this history at scale.

</domain>

<decisions>
## Implementation Decisions

### Global Timeline View
- A new "History" or "Audit" tab in the dashboard.
- Server-side pagination (`skip`/`limit`) is mandatory to handle thousands of records.
- Filters: `node_id`, `status`, `job_guid` (search), and date range.
- Real-time updates: The timeline should refresh or allow manual refresh to show new executions as they complete.

### Retention & Pruning
- Config-driven: `history_retention_days` (default: 30) stored in the `Config` table.
- Background Reaper: A new recurring task in `scheduler_service.py`.
- Batch Deletion: To avoid SQLite locking and Postgres transaction timeouts, deletions must happen in chunks (e.g., 1000 records per transaction).
- Output Log Cleanup: Pruning must ensure the `output_log` (which can be large) is physically removed from disk/DB.

### Performance & Indexing
- Composite indices are required for the most common query patterns:
  - `(node_id, started_at DESC)` for node-specific history.
  - `(job_guid, started_at DESC)` for job-specific history.
  - `(started_at DESC)` for the global timeline.

### API Structure
- `GET /api/executions`: Global list with query params for filtering and pagination.
- `DELETE /api/executions/prune`: Manual trigger for the reaper (admin only).
- `GET /api/stats/history`: Summary stats (e.g., total executions in last 24h, success rate).

</decisions>

<specifics>
## Specific Ideas

- The "History" view should allow clicking through to the same log viewer developed in Phase 1.
- Add a "Duration" column to the history table (calculated as `completed_at - started_at`).
- Retention should be aggressive by default (30 days) to prevent disk space issues on small nodes/servers.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ExecutionRecord` ORM model in `db.py`.
- `ExecutionRecordResponse` Pydantic model in `models.py`.
- `scheduler_service.py`: Already handles heartbeat monitoring and job timeouts; perfect for the history reaper.
- `Config` table: Already used for system-wide settings.

### Established Patterns
- FastAPI dependency injection for DB sessions.
- Pydantic models for API responses.
- React `Table` components for data display.

### Integration Points
- `puppeteer/agent_service/services/scheduler_service.py`: Add `prune_history` task.
- `puppeteer/agent_service/main.py`: Add `/api/executions` endpoints.
- `puppeteer/dashboard/src/components/`: New `History.tsx` component.
- `puppeteer/migration_v15.sql`: Add composite indices.

</code_context>

<deferred>
## Deferred Ideas

- Export to CSV/JSON: Keep it for a future "Reporting" phase.
- Advanced log searching (grep within output logs): Deferred due to performance complexity.

</deferred>

---

*Phase: 03-execution-history*
*Context gathered: 2026-03-05*
