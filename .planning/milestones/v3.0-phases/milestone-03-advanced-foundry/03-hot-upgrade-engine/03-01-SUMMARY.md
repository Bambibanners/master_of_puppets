# Plan 03-01 Summary: Orchestrator Schema & Staging API

**Status:** Complete
**Date:** 2026-03-05

## Actions Taken
- Updated `puppeteer/agent_service/db.py` to add `pending_upgrade` and `upgrade_history` fields to the `Node` ORM model.
- Implemented `POST /api/nodes/{node_id}/upgrade` in `puppeteer/agent_service/main.py`.
    - Fetches capability recipe and expands `{{ARTIFACT_URL}}`.
    - Signs the final recipe using `SignatureService` (Ed25519).
    - Stores the signed task in the node's `pending_upgrade` column.
    - Transitions node status to `UPGRADING`.
- Created `puppeteer/migration_v21.sql` with idempotent schema updates.

## Verification Results
- Python verification script confirmed presence of new fields in the `Node` ORM model.
- Manual logic review confirmed correct signature integration and macro expansion.
