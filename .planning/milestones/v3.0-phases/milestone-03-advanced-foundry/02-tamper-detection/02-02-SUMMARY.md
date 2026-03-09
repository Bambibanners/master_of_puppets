# Plan 02-02 Summary: Enrollment & Expectation Logic

**Status:** Complete
**Date:** 2026-03-05

## Actions Taken
- Added `EnrollmentTokenCreate` Pydantic model to `puppeteer/agent_service/models.py` to allow linking tokens to templates.
- Updated `create_enrollment_token` endpoint in `main.py` to accept and persist `template_id`.
- Updated `enroll_node` endpoint in `main.py` to automatically initialize a node's `expected_capabilities`.
    - If a token has a `template_id`, the system loads the template and its runtime blueprint.
    - All tools defined in the blueprint are added to the node's "Authorized" capability list.

## Verification Results
- `grep` verified presence of new token and enrollment logic in `main.py`.
- Logic review confirmed that expected capabilities are derived directly from the blueprint tool IDs.
