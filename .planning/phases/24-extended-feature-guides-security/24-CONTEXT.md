# Phase 24: Extended Feature Guides & Security - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Write three operator feature guides (job scheduling, RBAC, OAuth/authentication) and the complete Security & Compliance section (overview, mTLS, RBAC hardening, audit log, air-gap operation). Adds a standalone RBAC permission reference page. Also adds a Security section overview page that frames the defence-in-depth model. Phase 23 locked the nav — this phase fills in the Feature Guides → Platform Config slots (rbac.md, oauth.md, job-scheduling.md) and the entire Security section.

</domain>

<decisions>
## Implementation Decisions

### Security guide reader level

- **Assumed knowledge:** Novice operator — knows what TLS and Docker are, has run `docker compose` before, but has never touched PKI (no prior OpenSSL or cert knowledge assumed)
- Define all PKI terms on first use: CA, CRL, CSR, enrollment, etc.
- Include background boxes before complex procedures where needed
- Commands are fully explained — not just shown

### Security section structure

- **Opens with a Security Overview page** (`security/index.md`) before the individual guides
- Overview content: 2–3 paragraphs explaining the defence-in-depth model (how mTLS + Ed25519 + RBAC + audit log form layered security), one Mermaid diagram showing the layers, then a table of contents to the individual guides
- Overview includes a **Compromise Scenarios table**: orchestrator compromised (Ed25519 still blocks unsigned scripts), node compromised (mTLS + container isolation limits blast radius), credential leaked (token_version invalidation)
- Overview frames each control in terms of the threat it mitigates

### Command formatting

- Sensitive values (JOIN_TOKEN, private keys, cert paths, secrets) use `<PLACEHOLDER>` syntax in all code blocks
- Example: `JOIN_TOKEN=<YOUR_JOIN_TOKEN> docker compose up -d`
- Consistent across all Security and Feature Guide pages in this phase

### Security risk callouts

- Use `!!! danger` admonition for hard limits and irreversible actions (consistent with Phase 23 pattern)
- Use `!!! warning` for operational risks (e.g., weak JWT secret, private key on disk)
- No separate "Security Warning" summary sections — inline admonitions at the point of risk

### mTLS guide

- **Full CA setup covered here** — generating Root CA, creating JOIN_TOKEN, initial node enrollment. Setup & deployment guide (Phase 22) cross-links to this guide for the security-focused explanation
- **Cert rotation:** Full step-by-step with verification commands after every step — numbered steps, expected output shown, operator can't skip a verification step
- **Point of no return (revoke old cert):** Both a prerequisites checklist at the start of the rotation section AND a `!!! danger` admonition immediately before the revoke command
  - Checklist: "Before starting cert rotation, verify: [ ] new cert enrolled, [ ] node shows as Active in dashboard"
  - Danger box: "After this step, the old certificate is permanently revoked. Ensure the node has successfully enrolled with its new cert before proceeding."

### RBAC guide split (FEAT-04 vs SECU-02)

- **Task-split by audience purpose:**
  - FEAT-04 (`feature-guides/rbac.md`) = "Using RBAC" — UI workflow: create users, assign roles, manage service principals through the dashboard. Operational guide.
  - SECU-02 (under Security section) = "RBAC Hardening" — which permissions to grant per role, least-privilege patterns, what to audit. Prescriptive security guidance.
- **Service principals:** Dedicated H2 section within FEAT-04 (not woven into user management) — machine identity vs human identity is a distinct concept. Cross-link from OAuth guide.
- **Permission matrix:** Standalone reference page `feature-guides/rbac-reference.md` with the full table of which permissions each role has by default. Both FEAT-04 and SECU-02 link to it. Neither guide is table-heavy.

### Job scheduling guide (FEAT-03)

- **Cron syntax:** Brief intro (one paragraph explaining 5-field format + MoP-specific fields: second, timezone) + reference table of common patterns (every 5 min, daily at 2am, weekdays only, etc.). Link to an external cron visual generator for complex expressions. Not a cron tutorial.
- **Node targeting:** Covers both targeting modes side by side — capability targeting (OS family, runtime tags) and explicit node/group targeting. Comparison helps operators choose the right model.
- **Staging review:** Brief recap paragraph + cross-link to mop-push guide ("Scheduled jobs go through the same DRAFT→ACTIVE lifecycle. See the mop-push guide for the full Staging view walkthrough."). No full duplication.

### OAuth / authentication guide (FEAT-05)

- **Token lifecycle:** Full coverage — expiry (how long, how to check), forced revocation (password change invalidates all sessions via `token_version`), service principal tokens vs user tokens, how to revoke a specific session
- **Device flow:** Conceptual explanation (what RFC 8628 device flow is, why MoP uses it — no redirect URI needed in CLI context) + cross-link to mop-push guide for step-by-step. OAuth guide owns the "why", mop-push guide owns the "how".
- **CI/CD integration section:** Practical section — create service principal, generate API key, set as CI secret, example `curl` / `mop-push` command. Covers the machine-auth pipeline use case. Fits here because it's about machine identity/auth.

### Air-gap guide (SECU-04)

- **Format:** Narrative walkthrough (each area: package mirroring setup, offline build validation, outbound network restrictions) with a printable summary checklist at the end for audit mode
- **Offline state verification:** Includes a concrete test procedure — build with `--no-cache` while outbound network is blocked and confirm success
- **Post-setup package additions:** Dedicated section on the upload workflow (admin uploads .whl or .deb to the mirror sidecar after initial setup)
- **Docs container offline:** Brief section confirming MkDocs container is already offline-capable (privacy + offline plugins) and noting how to build the docs image without external deps
- **"What still requires internet" section:** Explicit list of what cannot be air-gapped — Cloudflare tunnel (must be replaced with on-prem alternative for full air-gap), initial base image pulls, any external Smelter lookups. Enterprise operators need to know exactly what to substitute.

### Claude's Discretion

- Section ordering within each guide beyond the structural decisions above
- Exact Mermaid diagram style for the Security overview
- Internal cross-linking strategy between feature guides
- Whether audit log guide uses a table of all event types or a structured list
- Tone and formatting conventions within the novice-level reading target

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets

- `docs/mkdocs.yml`: Phase 23 established the 7-section nav with Feature Guides and Security sections. Phase 24 fills in their sub-pages. Stub index.md files already exist in Security and Runbooks sections.
- `docs/docs/security/index.md`: Currently a stub ("Coming soon") — Phase 24 replaces this with the Security Overview page
- `docs/docs/feature-guides/`: Directory exists with foundry.md and mop-push.md — add rbac.md, oauth.md, job-scheduling.md, rbac-reference.md
- `mop_sdk/cli.py`: mop-push CLI source — reference for accurate command syntax in job scheduling and OAuth guides
- `puppeteer/agent_service/auth.py`: JWT creation/verification, token_version logic — source of truth for OAuth guide's token lifecycle section
- `puppeteer/agent_service/db.py`: `RolePermission` table + permission seeding — source of truth for the canonical permission matrix in rbac-reference.md
- `puppeteer/agent_service/pki.py`: Root CA and client cert signing — source of truth for mTLS guide's CA setup procedure

### Established Patterns

- `!!! danger` / `!!! warning` / `!!! tip` admonitions already configured and used in Phases 22–23
- Admonition-as-gotcha pattern: inline at the point of the gotcha, not in a separate section
- No screenshots — reference actual UI labels as they appear in the dashboard
- `mkdocs build --strict` enforced — all nav entries must have corresponding files before committing
- Privacy + offline plugins already enabled — no external CDN assets at runtime
- `<PLACEHOLDER>` syntax for sensitive values (established this phase)

### Integration Points

- `docs/mkdocs.yml`: Add sub-pages under Feature Guides (job-scheduling.md, rbac.md, oauth.md, rbac-reference.md) and Security section (overview already stub, add mtls.md, rbac-hardening.md, audit-log.md, air-gap.md)
- `docs/docs/feature-guides/`: 4 new files
- `docs/docs/security/`: index.md (replace stub) + 4 new files

</code_context>

<specifics>
## Specific Ideas

- The mTLS guide should be thorough enough that an operator who has never touched PKI can complete a full cert rotation without calling anyone for help — "full step-by-step with verification at every step" was explicitly chosen
- The Compromise Scenarios table in the Security Overview was specifically requested — enterprise operators need honest answers to "what if the orchestrator is compromised?"
- The CI/CD integration section in the OAuth guide is the primary use case for many enterprise operators; it should be practical (actual commands, not pseudo-code)
- The air-gap guide's "what still requires internet" section is explicitly for enterprise operators who need to know what to substitute for a fully isolated deployment — be honest and complete, not optimistic

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 24-extended-feature-guides-security*
*Context gathered: 2026-03-17*
