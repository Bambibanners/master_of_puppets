# Phase 4: Environment Tags - Context

**Gathered:** 2026-03-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 moves the system from "ad-hoc" node tagging to "governed" environment segmentation. It allows operators to override node-reported tags and introduces a strict isolation layer for tags prefixed with `env:`.

This phase does not include dynamic auto-scaling or advanced scheduling based on load; it focuses purely on placement correctness and operator control.

</domain>

<decisions>
## Implementation Decisions

### Operator Overrides
- A new `operator_tags` column will be added to the `Node` table.
- When `operator_tags` is present, it **replaces** the node-reported tags in all job matching and dashboard displays. If null, the system falls back to node-reported tags.
- This gives operators ultimate authority over node placement without requiring node-level config changes.

### Environment Convention (`env:`)
- Any tag starting with `env:` (e.g., `env:prod`, `env:dev`, `env:staging`) is treated as a **Strict Environment Tag**.
- **Rule 1 (Job Requirement)**: If a job has a `target_tag` of `env:prod`, it **must only** run on a node that has the `env:prod` tag.
- **Rule 2 (Node Restriction)**: If a node has an `env:prod` tag, it **must not** run any job that does not explicitly include `env:prod` in its `target_tags`. This prevents "blind" jobs (no tags) from landing on production nodes.

### Matching Logic (Simplified)
- Node Effective Tags = `operator_tags` ?? `node_reported_tags`
- Job Matching:
    1.  Standard check: Does Node have ALL Job tags? (Existing logic)
    2.  Strict check: Does Node have any `env:X` tags that are NOT in Job's tags? If yes, REJECT.
    3.  Strict check: Does Job have any `env:X` tags that are NOT in Node's tags? If yes, REJECT.

### Dashboard UX
- The "Edit Node" modal will gain a "Tags" field.
- Tags will be displayed as badges. `env:` tags will use distinct semantic colors:
    - `env:prod` -> Red/Rose
    - `env:staging` -> Amber/Yellow
    - `env:test` -> Blue/Indigo
    - `env:dev` -> Gray/Zinc (default)

</decisions>

<specifics>
## Specific Ideas

- Add a `tags_updated_at` timestamp to the Node table to track when operator overrides were last changed.
- Use a simple comma-separated input for the tag editor in the dashboard for now, keeping it lean.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `NodeConfig` model in `models.py`.
- `update_node_config` endpoint in `main.py`.
- `JobService.pull_work` matching loop.
- `Badge` component in dashboard.

### Integration Points
- `puppeteer/agent_service/db.py`: Add `operator_tags` to `Node` class.
- `puppeteer/agent_service/services/job_service.py`: Update `pull_work` matching logic.
- `puppeteer/dashboard/src/views/Nodes.tsx`: Update list and edit modal.
- `puppeteer/migration_v17.sql`: Schema update for Phase 4.

</code_context>

---

*Phase: 04-environment-tags*
*Context gathered: 2026-03-05*
