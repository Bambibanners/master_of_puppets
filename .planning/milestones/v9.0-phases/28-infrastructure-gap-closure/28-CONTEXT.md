# Phase 28: Infrastructure Gap Closure - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Restore the `privacy` and `offline` MkDocs plugins to `docs/mkdocs.yml`. These were removed in regression commit ab25961 during Phase 22 execution, but were an explicit requirement from Phase 20 (both named in the Phase 20 CONTEXT.md and required for INFRA-06). The fix is surgical — two plugin entries re-added to mkdocs.yml. No content changes, no new pip dependencies (both plugins ship with mkdocs-material).

</domain>

<decisions>
## Implementation Decisions

### Plugin configuration
- Both plugins use default settings — no custom options
- Ordering: `search` → `privacy` → `offline` → `swagger-ui-tag`
- This matches MkDocs Material recommended ordering: privacy fetches external assets, offline then bundles them

### Plugin annotation
- Add a comment above the privacy + offline entries in mkdocs.yml:
  `# privacy + offline: required for air-gap / offline operation (INFRA-06) — do not remove`
- Prevents future regression by making the intent explicit to anyone editing the file

### Verification method
- Build the docs Docker image: `docker compose build docs`
- After successful build, run a grep check against the built HTML to confirm zero external CDN references:
  `docker run --rm <image> grep -rq 'fonts.googleapis.com\|cdn.jsdelivr.net\|cdnjs.cloudflare.com' /usr/share/nginx/html && echo FAIL || echo PASS`
- This check lives in the plan task only — no new script files added to the repo
- Both build success AND the grep passing are required to close INFRA-06

### Requirements closure
- Mark INFRA-06 as complete (`[x]`) in `.planning/REQUIREMENTS.md` once the fix is verified
- INFRA-06 is the only remaining unchecked infrastructure requirement for v9.0

### Air-gap guide verification
- Read `docs/docs/security/air-gap.md` and confirm it references the privacy + offline plugin setup correctly
- If the guide references these plugins (or relies on CDN-free operation), verify the content is consistent with the restored config
- No content rewrite expected — this is a consistency check only

### Claude's Discretion
- Exact wording of the comment in mkdocs.yml
- Whether to rebuild the docs container as part of verification or use `docker build` directly

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/mkdocs.yml`: Target file — add two plugin entries between `search` and `swagger-ui-tag`
- `docs/Dockerfile`: Already runs `mkdocs build --strict` in builder stage — no changes needed
- `docs/requirements.txt`: `mkdocs-material==9.7.5` already installed — privacy + offline plugins are bundled, no new pip packages required

### Established Patterns
- `docs/requirements.txt` pins exact versions — no changes needed for this fix
- `mkdocs build --strict` is enforced in the builder stage — any plugin misconfiguration will fail the Docker build immediately

### Integration Points
- `docs/mkdocs.yml` is the sole change point
- `.planning/REQUIREMENTS.md` gets INFRA-06 checked off
- `docs/docs/security/air-gap.md` read for consistency check (no edit expected)

</code_context>

<specifics>
## Specific Ideas

- The regression is documented: commit ab25961 removed exactly these two lines from the plugins list. The fix is restoring them.
- The grep pattern to check for CDN refs should cover at minimum: `fonts.googleapis.com`, `cdn.jsdelivr.net`, `cdnjs.cloudflare.com`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 28-infrastructure-gap-closure*
*Context gathered: 2026-03-17*
