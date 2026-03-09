# Phase 4: Environment Tags - Research

**Gathered:** 2026-03-05
**Status:** ## RESEARCH COMPLETE

## Summary
Phase 4 (Environment Tags) introduces a formal mechanism for segmenting the node fleet using operator-assigned labels. The primary goal is to prevent "cross-talk" between environments (e.g., a dev job running on a prod node) by enforcing strict tag matching for designated "environment" tags.

## Existing Implementation
- **Node Tags**: Nodes currently report their own tags via `HeartbeatPayload`. These are stored as a JSON string in `Node.tags`.
- **Job Tags**: Jobs can specify `target_tags`.
- **Matching Logic**: `JobService.pull_work` performs a simple "all required tags must be present on node" check:
  ```python
  if not all(t in node_tags_list for t in req_tags):
      continue
  ```
- **Limitations**:
    - No central operator override for node tags.
    - No "exclusive" matching (a prod node will still pick up untagged jobs).
    - No visual management of tags in the dashboard beyond display.

## Requirement Analysis
- **TAG-01**: Operator-assignable tags. Requires extending `NodeConfig` and `update_node_config` API.
- **TAG-02**: Environment-specific targeting. Jobs must be able to request an environment.
- **TAG-03**: Strict enforcement. Nodes with `env:*` tags must REJECT jobs that don't match the specific environment.
- **TAG-04**: Dashboard integration. Visual badges and an editor for node tags.

## Technical Strategy
1.  **Persistence**: Add `operator_tags` column to `Node` table OR use the existing `tags` column but distinguish between node-reported and operator-assigned. *Decision: Operator-assigned tags should probably override or merge with node-reported tags. To keep it simple and follow the objective, we'll implement operator-assigned tags that overwrite the node's own reporting if set.*
2.  **API**: Extend `PATCH /nodes/{node_id}` to accept `tags`.
3.  **Strict Environment Logic**:
    - Convention: Tags starting with `env:` are treated as environment segments.
    - If a Node has an `env:X` tag:
        - It **must only** accept jobs that have `env:X` in their `target_tags`.
        - It **must reject** jobs with no `env:` tag.
        - It **must reject** jobs with a different `env:Y` tag.
4.  **Frontend**:
    - Update `NodeConfig` modal to include a tag editor (comma-separated string or tag input).
    - Add color-coded badges for `env:` tags in node lists.

## Common Pitfalls
- **Tag Merging**: If a node reports `linux` and the operator assigns `prod`, the node should ideally have both. However, operator intent should usually win.
- **Race Conditions**: Node heartbeats might overwrite operator tags if not handled carefully. `JobService.report_heartbeat` needs to respect operator-assigned values.
- **Empty Tags**: A job with no tags should run on any node *unless* that node is environment-restricted.

## Implementation Plan (Draft)
- **Plan 4.1**: DB & Models. Add `operator_tags` to `Node` table. Update `NodeConfig` and `NodeResponse` Pydantic models.
- **Plan 4.2**: Backend API & Heartbeat. Update `update_node_config` to save tags. Update `report_heartbeat` to merge or prioritize operator tags.
- **Plan 4.3**: Strict Enforcement. Update `pull_work` logic to implement `env:` segment isolation.
- **Plan 4.4**: Frontend UI. Add tag editor to Node modal. Add color-coded environment badges.

---
*Phase: 04-environment-tags*
*Context: Master of Puppets Reliability Milestone*
