# Phase 3: Headless Management & SDK - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 3 focuses on consolidating the platform's machine-facing interfaces into a formal Python SDK and comprehensive API documentation. This allows developers to integrate Master of Puppets into their own tools, scripts, and workflows with minimal effort.

## SDK Goals
The SDK should be a lightweight wrapper around the REST API, providing:
1.  **Authentication**: Support for both JWT (Username/Password) and API Keys (Service Principals).
2.  **Job Lifecycle**: `create_job`, `get_job_status`, `list_jobs`, `cancel_job`.
3.  **Automatic Signing**: The SDK should be able to load a private Ed25519 key and sign scripts automatically before submission.
4.  **Node Monitoring**: `list_nodes`, `get_node_details`.
5.  **Reactive Hooks**: `fire_signal`, `fire_trigger`.

## Proposed SDK Structure
```python
from mop_sdk import MOPClient

client = MOPClient(base_url="https://mop.local", api_key="mop_...")

# Simple job submission
job = client.submit_python_job(
    name="Clean Logs",
    script="import os; os.remove('/tmp/log.txt')",
    tags=["prod"],
    private_key_path="./my_key.pem"
)

# Wait for completion
result = client.wait_for_job(job.guid)
print(result.output)
```

## Documentation Strategy
- **API_REFERENCE.md**: A dedicated file in `docs/` that lists every endpoint, required headers, request schemas, and sample responses.
- **SDK_GUIDE.md**: A guide on how to install and use the Python SDK.
- **EXAMPLES/ folder**: A collection of scripts showing real-world usage (e.g., "Deploy via GitHub Actions", "Daily Backup Script").

## Potential Pitfalls
- **SSL Verification**: The orchestrator uses self-signed or internal CAs by default. The SDK must handle CA certificate paths or allow disabling verification (with big warnings).
- **Large Log Handling**: Getting job output can return a lot of data. The SDK should handle streaming or truncation gracefully.
- **Dependency Bloat**: Keep the SDK dependencies minimal (e.g., `httpx`, `pydantic`, `cryptography`).

## Implementation Plan
- **Plan 03-01**: SDK Foundation. Implement the `MOPClient` with authentication and job management.
- **Plan 03-02**: Automatic Signing Integration. Build Ed25519 signing into the SDK's job submission flow.
- **Plan 03-03**: Formal API Reference. Generate and polish the `API_REFERENCE.md` and `SDK_GUIDE.md`.

---
*Phase: 03-headless-sdk*
*Context: Master of Puppets Automation Milestone*
