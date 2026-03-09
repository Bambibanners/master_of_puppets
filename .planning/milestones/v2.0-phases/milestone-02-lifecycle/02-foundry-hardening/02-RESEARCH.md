# Phase 2: Foundry Hardening - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 2 (Foundry Hardening) focuses on making the node image building process robust, non-blocking, and resource-aware. While basic async execution is present, the service lacks protection against concurrent build overload and still uses blocking I/O for file operations.

## Current Implementation Analysis
- **Async Subprocesses**: `FoundryService.build_template` correctly uses `asyncio.create_subprocess_exec` for the build and push commands.
- **Blocking I/O**: `shutil.copytree`, `shutil.rmtree`, and `os.makedirs` are called directly on the main event loop. For large directories or slow disks, this will block the API server.
- **Concurrency**: There is no limit on how many builds can run simultaneously. Multiple concurrent build requests could exhaust disk space in `/tmp` or CPU/RAM on the host.
- **Error Surfacing**: While it logs errors, the `ImageResponse` only returns a truncated error message. The full build log is lost if not captured from stdout/stderr.

## Hardening Strategies
1.  **Concurrency Control**: Use an `asyncio.Semaphore(2)` (default to 2 concurrent builds) to prevent resource exhaustion.
2.  **Non-blocking File I/O**: Use `asyncio.to_thread` for all `shutil` and `os` operations to ensure the event loop stays responsive.
3.  **Enhanced Build Logs**: Capture both stdout and stderr during the build. In case of failure, store the last 100 lines of the build log in the database or return it in the response for better debugging.
4.  **Temp Directory Cleanup**: Ensure build directories are unique and always cleaned up, even in case of catastrophic service failure (e.g., using a more robust context manager pattern).

## Technical Strategy
- Introduce a class-level `_build_semaphore` in `FoundryService`.
- Wrap directory setup/teardown and copying in `asyncio.to_thread`.
- Refine the build command execution to merge and store output for failure reporting.

---
*Phase: 02-foundry-hardening*
*Context: Master of Puppets Milestone 2*
