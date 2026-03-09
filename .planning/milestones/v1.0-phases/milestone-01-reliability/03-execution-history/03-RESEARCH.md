# Phase 3: Execution History - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 3 (Execution History) will expand the existing `ExecutionRecord` capture into a system-wide auditing and retention framework. The architecture will transition from per-job execution lists to a global, queryable timeline with automated lifecycle management.

## Standard Stack
- **Database**: SQLite (Dev) / Postgres (Prod) via SQLAlchemy.
- **Scheduling**: APScheduler (existing `scheduler_service`) for maintenance tasks.
- **Frontend**: React + `date-fns` for time-series formatting.
- **API**: FastAPI with server-side pagination (`skip`/`limit`).

## Architecture Patterns
- **Global Audit Timeline**: A cross-job view querying `ExecutionRecord` directly, rather than nesting under jobs.
- **Config-Driven Retention**: Pruning logic must read `history_retention_days` from the `Config` table.
- **Batch Maintenance**: Deletions in the background reaper should be batched (e.g., 1000 records) to avoid transaction timeouts.
- **Composite Indexing**: Optimized queries require composite indices on `(node_id, started_at)` and `(job_guid, started_at)`.

## Don't Hand-Roll
- **Cron Logic**: Use the established `scheduler_service` patterns.
- **Relative Time Formatting**: Use `date-fns` (e.g., `formatDistanceToNow`).
- **Pagination**: Use standard SQLAlchemy `offset()` and `limit()`.

## Common Pitfalls
- **Disk Bloat**: Output logs (up to 1MB each) can accumulate rapidly. Retention must be aggressive by default (30 days).
- **SQLite Locking**: Long-running deletes can block node check-ins. Batching is mandatory.
- **Timezone Drift**: All timestamps must remain in UTC; the UI handles local display conversion.

## Code Examples
### Pruning Pattern (scheduler_service.py)
```python
async def prune_execution_history(self):
    async with db_module.AsyncSessionLocal() as session:
        retention = await self._get_config(session, 'history_retention_days', '30')
        cutoff = datetime.utcnow() - timedelta(days=int(retention))
        await session.execute(
            delete(ExecutionRecord).where(ExecutionRecord.started_at < cutoff)
        )
        await session.commit()
```

### API Timeline (main.py)
```python
@app.get("/executions")
async def list_global_history(node_id: Optional[str] = None, status: Optional[str] = None):
    # Standard query + filters + pagination pattern
```

---
*Phase: 03-execution-history*
*Context: Master of Puppets Reliability Milestone*
