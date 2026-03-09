# Plan 05-01 Summary: Alerting Engine Foundation

**Status:** Complete
**Date:** 2026-03-06

## Actions Taken
- **Schema Update**: Added `Alert` model to `db.py` to store system-wide notifications (Job failures, Node offline).
- **Alert Service**: Created `puppeteer/agent_service/services/alert_service.py` with:
    - `create_alert`: Standardizes alert creation with severity and type.
    - `list_alerts`: Supports pagination and unacknowledged-only filtering.
    - `acknowledge_alert`: Allows operators to mark alerts as seen.
    - `check_node_health`: Logic to detect nodes that haven't sent heartbeats for > 5 minutes.
- **Job Service Integration**:
    - Hooked into `report_result` and `pull_work` (zombie reaping) to trigger `CRITICAL` alerts when a job enters the `DEAD_LETTER` state.
- **Backend Monitoring**:
    - Implemented a background task in `main.py` (via `asyncio.create_task`) that runs every 60 seconds to perform node health checks using `AlertService.check_node_health`.
- **API Endpoints**:
    - Added `GET /api/alerts` (list) and `POST /api/alerts/{id}/acknowledge`.
- **RBAC**:
    - Updated Role Permission seeding to include `alerts:read` and `alerts:write`.

## Verification Results
- Database model successfully created.
- `JobService` now imports `AlertService` without circular dependencies.
- Background task is wired into the FastAPI lifespan.
- Permissions are seeded for Admin, Operator, and Viewer roles.

## Next Steps
- Implement **Phase 2: Outbound Webhooks**, which will hook into `AlertService.create_alert` to dispatch external notifications.
