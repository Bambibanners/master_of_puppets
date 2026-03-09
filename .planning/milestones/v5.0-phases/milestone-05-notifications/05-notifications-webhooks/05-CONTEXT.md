# Phase 05-01: Alerting Engine

## Objective
Implement the core alerting logic to detect and record critical system events: exhausted job retries (permanent failures) and unexpected node offline events.

## Context
Master of Puppets currently records failures but does not have a centralized "Alert" entity or notification dispatch logic. This phase will establish the backend infrastructure for alerts before we add external integrations like webhooks.

## Requirements Covered
- **NOTF-01**: Operator receives alert when a job exhausts all retries.
- **NOTF-02**: Operator receives alert when a node goes offline unexpectedly.

## Strategy
1. **Schema Update**: Introduce an `Alert` model in `db.py` to store system alerts.
2. **Alert Dispatcher**: Create a central service to "emit" alerts.
3. **Job Watcher**: Hook into the `job_service` to detect when a job enters a final failure state (`DEAD_LETTER`).
4. **Heartbeat Watcher**: Enhance the heartbeat/node monitoring logic to detect missed heartbeats beyond a threshold and generate alerts.
5. **Dashboard View**: Add a basic Alerts notification bell or list to the dashboard.

## Key Files
- `puppeteer/agent_service/db.py` (Models)
- `puppeteer/agent_service/models.py` (Schemas)
- `puppeteer/agent_service/services/job_service.py` (Failure detection)
- `puppeteer/agent_service/main.py` (API endpoints for alerts)
