# Phase 1: Pipeline Core Fixes - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Initial research confirms that many of the critical backend bugs (BUG-1 through BUG-4) have been resolved in the current codebase. However, some refinements are needed to fully satisfy the milestone requirements and ensure the pipeline is robust.

## Backend Status
- **BUG-1 (Job Definitions)**: Resolved. `/job-definitions` calls `scheduler_service.list_job_definitions`.
- **BUG-2 (NodeResponse)**: Resolved. `list_nodes` returns `capabilities`, `tags`, and limits.
- **BUG-3 (SemVer Comparison)**: Resolved. `JobService.pull_work` uses `packaging.version.Version`.
- **BUG-4 (Last Built)**: Resolved. `last_built_at` is present in DB, models, and updated in `foundry_service.py`.
- **GAP-1 (Delete Endpoints)**: Resolved. `DELETE` endpoints for blueprints, templates, and job definitions exist.
- **GAP-10 (Upload Key)**: Resolved. `upload_public_key` persists to `Config` table.

## Remaining Gaps (Phase 1 Focus)
While the "Core Fixes" are largely in place, the following refinements are needed to complete this phase:
1.  **Foundry Image Integrity**: `foundry_service.py` currently only copies `environment_service/` but misses `requirements.txt`. The generated Dockerfile needs to install these dependencies to ensure the built image can actually run.
2.  **Delete Safety**: `delete_template` should ideally check if any active nodes are using the image before allowing deletion (though images are immutable once pulled, cleanup is better).
3.  **Frontend Status Check**: We need to verify if the frontend is actually displaying the new fields (capabilities, last built at) and if the delete buttons are present.

## Technical Strategy
1.  **Refine Foundry Build**: Update `FoundryService.build_template` to copy `requirements.txt` and include `RUN pip install` in the Dockerfile.
2.  **Verify Frontend Integration**: Inspect `Templates.tsx` and `Nodes.tsx` to ensure BUG-2 and BUG-4 fixes are surfaced to the user.

---
*Phase: 01-pipeline-fixes*
*Context: Master of Puppets Milestone 2*
