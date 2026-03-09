# Phase 1: Automation APIs - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 1 focuses on transitioning Master of Puppets from a human-centric dashboard into a headless automation platform. The primary goal is to provide stable, secure, and machine-friendly endpoints for CI/CD pipelines (GitHub Actions, GitLab CI, etc.) to trigger jobs without requiring full administrative access.

## Existing Integration Hooks
- **Service Principals**: Machine-to-machine accounts with API keys already exist.
- **Job Creation API**: `POST /jobs` exists but requires full `JobCreate` payloads and permissions.
- **Scheduled Jobs**: Can be triggered manually from the UI, but lack a dedicated automation-friendly "Fire Now" endpoint.

## Proposed: Trigger System
Instead of CI/CD systems knowing the full job configuration (scripts, tags, etc.), we will implement a **Trigger** abstraction.

1. **Trigger Definition**: An admin defines a Trigger in MOP.
    - `id`: A unique, immutable slug (e.g., `prod-deployment-trigger`).
    - `job_definition_id`: Links to an existing `ScheduledJob`.
    - `payload_overrides`: (Optional) Map of keys that the trigger can override in the template.
    - `secret_token`: A dedicated key for this specific trigger.
    - `is_active`: Toggle for maintenance.

2. **Trigger API**:
    - `POST /api/trigger/{slug}`
    - Authentication: `X-MOP-Trigger-Key` header.
    - Payload: Simple JSON with parameters to be injected into the job script/payload.

3. **Advantages**:
    - **Security**: CI/CD pipelines only hold a trigger key, not a master admin key. They can only fire the specific job bound to that trigger.
    - **Simplicity**: One `curl` command without needing to construct complex `JobCreate` objects.
    - **Observability**: Triggers can be audited separately in the `AuditLog`.

## Technical Strategy
1. **Schema Extension**: Add `triggers` table to `db.py`.
2. **Trigger Service**: A new service to handle Slug-to-Job resolution and payload merging.
3. **API Implementation**:
    - `POST /api/trigger/{slug}`: The public-facing automation endpoint.
    - `GET/POST/DELETE /api/admin/triggers`: Management endpoints for operators.

## Potential Pitfalls
- **Rate Limiting**: CI/CD pipelines can sometimes go rogue. Webhook endpoints must have per-IP or per-token rate limits.
- **Payload Injection**: Need to ensure that overrides provided via the trigger are safely merged into the job payload.

---
*Phase: 01-automation-apis*
*Context: Master of Puppets Automation Milestone*
