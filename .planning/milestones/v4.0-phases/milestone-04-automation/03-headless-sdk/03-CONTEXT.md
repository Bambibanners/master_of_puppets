# Phase 3: Headless Management & SDK - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 is the **Accessibility** layer. It doesn't add new backend functionality but rather "packages" the existing system for external consumption.

**In Scope:**
- Creation of a Python-based SDK (`mop_sdk`).
- Integrated Ed25519 signing in the client.
- Comprehensive Markdown-based API and SDK documentation.
- Example automation scripts.

**Out of Scope:**
- Multi-language SDKs (Go, JS, etc.) - focused only on Python for now.
- Auto-generation of client code from OpenAPI (polishing manual client instead).

</domain>

<decisions>
## Implementation Decisions

### SDK Language
- **Python 3.10+**: Matches the orchestrator and node agent stack, allowing for shared logic if needed (e.g., signing).

### Core Dependency
- **`httpx`**: Chosen for its modern async support and excellent performance.
- **`cryptography`**: Required for Ed25519 signature generation.

### Documentation Location
- All machine-facing documentation will live in the `docs/` folder of the main repository.

### Signing Logic
- The SDK will load standard PEM-encoded private keys. It will support both unencrypted keys and those requiring a passphrase.

</decisions>

<specifics>
## Specific Ideas

- The `MOPClient` should have a `wait_for_job` method that polls the status endpoint with exponential backoff until a terminal state is reached.
- Add a `logging` integration so users can easily see what the SDK is doing.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `submit_job.py`: Contains the prototype signing and submission logic.
- `puppeteer/agent_service/models.py`: Defines the data structures the SDK should mirror.
- `puppeteer/agent_service/auth.py`: Informs how to perform JWT login.

### Integration Points
- `docs/API_REFERENCE.md`: New file.
- `mop_sdk/`: New folder for the library.

</code_context>

---

*Phase: 03-headless-sdk*
*Context gathered: 2026-03-05*
