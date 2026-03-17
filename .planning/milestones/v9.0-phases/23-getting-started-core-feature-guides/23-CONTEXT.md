# Phase 23: Getting Started & Core Feature Guides - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Write the operator-facing getting started walkthrough (install → enroll node → first job), a prerequisites guide, the Foundry feature guide (blueprints, wizard, Smelter, image lifecycle), and the mop-push CLI guide (install, login, key setup, push, publish). Also locks the top-level navigation architecture for all future documentation phases (24, 25).

</domain>

<decisions>
## Implementation Decisions

### Navigation architecture (locked for all future phases)

Top-level sections (6 total):
```
nav:
  - Home: index.md
  - Getting Started: ...
  - Feature Guides: ...
  - Security: ...
  - Runbooks: ...
  - Developer: ...
  - API Reference: ...
```

- **Runbooks** is its own top-level section — not nested under Security. Operators in a broken-system scenario must be able to find it immediately.
- Developer and API Reference sections already exist (Phase 22/21) — do not restructure them.

Getting Started sub-pages (granular, each step its own page):
```
Getting Started:
  - Prerequisites: getting-started/prerequisites.md
  - Install: getting-started/install.md
  - Enroll a Node: getting-started/enroll-node.md
  - First Job: getting-started/first-job.md
```

Feature Guides sub-sections (grouped by audience):
```
Feature Guides:
  - Operator Tools:
    - mop-push CLI: feature-guides/mop-push.md
    # Phase 24 adds: job-scheduling.md
  - Platform Config:
    - Foundry: feature-guides/foundry.md
    # Phase 24 adds: rbac.md, oauth.md
```

### Getting started walkthrough

- **Target audience:** Both homelab operators and enterprise admins — shared linear narrative with admonition callouts at branch points where the paths differ (e.g., TLS config, JOIN_TOKEN handling, existing CA)
- **Install path:** Docker Compose only — opinionated, single path. Include a callout that Podman Compose works as a drop-in alternative (the stack is designed to run under Podman too)
- **Structure:** Each sub-page is a focused linear section. No section-jumping required to complete the full flow
- **First job:** Dispatched entirely through the dashboard UI — no CLI required for the first-run experience. mop-push CLI is a separate Feature Guide
- **Prerequisites page:** Checklist format with a `verify with:` command for each prerequisite (e.g., `docker --version`, `podman-compose --version`). Reader confirms their environment before proceeding
- **Enterprise/homelab splits:** Admonition callouts inline at branch points — guide stays linear, variants are clearly labelled (e.g., `> **Enterprise:** If you have an existing CA...`)
- **End state:** Reader has a verified job result visible in the dashboard

### Foundry guide

- **Wizard walkthrough:** Numbered steps referencing actual UI labels visible in the dashboard — no screenshots (avoids stale images as UI evolves)
- **Coverage:** Full workflow — blueprint creation first (what is a blueprint, how to create runtime and network blueprints), then template composition via the 5-step wizard
- **Smelter depth:** Feature overview only — explains what Smelter does and what STRICT vs WARNING enforcement means in practical terms (build fails vs warning badge). Deep CVE scanning config and enforcement_mode live in Phase 24 Security section (link to it)
- **Image lifecycle:** Practical operator actions only — what each status (ACTIVE/DEPRECATED/REVOKED) means and how to change it from the dashboard. Enforcement mechanics (how the backend blocks enrollment/dispatch) stay in the Architecture guide

### mop-push CLI guide

- **Starting assumption:** Stack is running and at least one node is enrolled — guide opens with "Prerequisites: see Getting Started" link. Does not re-explain setup
- **OAuth login presentation:** Step-by-step with example CLI output — shows the command, device code prompt, browser URL, and what success looks like (token stored, ready to push)
- **Ed25519 key setup:** Covers keypair generation (`openssl genpkey` or `admin_signer.py`), registering the public key in the dashboard, and a brief private key security note (don't commit to git, use a secrets manager)
- **End state:** Full operator workflow — CLI push creates a DRAFT job, guide then directs to the dashboard Staging view for review, and walks through the Publish step. Reader ends with an ACTIVE job

### Claude's Discretion

- Exact admonition box labels and styling for homelab/enterprise callouts
- Mermaid diagrams or visual aids within guides (where helpful)
- Internal cross-linking strategy between guide pages
- Whether the index.md "Getting started" table is updated to point to the new granular pages

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `docs/mkdocs.yml`: Currently has `nav:` with Home, Developer, and API Reference sections. Phase 23 adds Getting Started and Feature Guides sections (and stubs Security and Runbooks for future phases)
- `docs/docs/index.md`: Existing placeholder with feature overview and a 4-entry table linking to setup-deployment, architecture, contributing, and API reference — update the table to point to the new getting-started pages
- `mop_sdk/cli.py`: `mop-push` supports `login`, `job push`, `job create` subcommands. `--url` flag or `MOP_URL` env var sets the base URL. The OAuth device flow, signing, and push workflow are all implemented here — guide can reference actual command syntax

### Established Patterns

- MkDocs content lives in `docs/docs/` (NOT `docs/` root)
- `mkdocs build --strict` enforced — all nav entries must have corresponding files before committing
- Privacy + offline plugins already enabled — no external CDN assets at runtime
- Admonitions (`admonition` + `pymdownx.details` extensions) already configured — use freely for callouts

### Integration Points

- `docs/mkdocs.yml`: Add Getting Started, Feature Guides, Security (stub), and Runbooks (stub) nav sections
- `docs/docs/getting-started/`: New directory with prerequisites.md, install.md, enroll-node.md, first-job.md
- `docs/docs/feature-guides/`: New directory with foundry.md, mop-push.md
- Security and Runbooks sections in nav will be stubs (empty or index-only) until Phases 24-25 fill them

</code_context>

<specifics>
## Specific Ideas

- Podman Compose support should be surfaced early in the install guide — it's not just a footnote. The stack is designed to run under Podman and operators deploying in enterprise environments (especially RHEL/Fedora-based) may default to Podman
- The getting started walkthrough must end with a visually confirmed job result in the dashboard — the success criterion is "confirmed job result visible in the dashboard", not just "job dispatched"
- The mop-push guide covers the complete operator loop (push → Staging → Publish) so the reader experiences the full DRAFT→ACTIVE lifecycle, not just the CLI half

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 23-getting-started-core-feature-guides*
*Context gathered: 2026-03-17*
