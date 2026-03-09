# Phase 2: Foundry Hardening - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 focuses on the stability and scalability of the "Foundry" image-building engine. It moves the build process from a "naive async" implementation to a "hardened" one that manages concurrency and protects the main event loop from blocking I/O.

This phase does not include adding new build tools or OS families; it is strictly about the reliability of the existing build engine.

</domain>

<decisions>
## Implementation Decisions

### Concurrency Management
- **Mechanism**: A static `asyncio.Semaphore` will be added to the `FoundryService` class.
- **Limit**: Set to 2 concurrent builds by default. This is enough for homelabs/small teams without overwhelming the host CPU/IO.
- **UX**: If the semaphore is full, the request will wait asynchronously until a slot opens.

### Non-blocking File Operations
- **Approach**: Use `asyncio.to_thread` for all `shutil` and `os` operations. 
- **Benefit**: Prevents the web server from becoming unresponsive during recursive directory copies or deletions.

### Build Log Capture
- **Mechanism**: Merge `stdout` and `stderr` into a single stream during the build command.
- **Reporting**: If a build fails, the last 10 lines of the build output will be included in the `status` field of the `ImageResponse` for immediate feedback in the dashboard.

### Unique Build Isolation
- **Mechanism**: Include a random suffix or the template ID in the build directory path to prevent collisions between rapid rebuilds of the same template.

</decisions>

<specifics>
## Specific Ideas

- Log the start and end of the semaphore wait time to track build queue pressure.
- Ensure the `build_dir` is always absolute and sanitized to prevent path traversal issues (though currently using `/tmp/` which is safe).

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FoundryService.build_template` method.
- `asyncio.create_subprocess_exec` usage.

### Integration Points
- `puppeteer/agent_service/services/foundry_service.py`: Primary target for all changes.

</code_context>

---

*Phase: 02-foundry-hardening*
*Context gathered: 2026-03-05*
