# Milestones

## v7.0 Advanced Foundry & Smelter (Shipped: 2026-03-16)

**Phases completed:** 5 phases (11–15), 34 plans

**Key accomplishments:**
- Compatibility Engine — OS-family tagging on tools, two-pass blueprint validation (OS mismatch + dep confirmation), real-time tool filtering in blueprint creation; 12/12 Playwright checks passed
- Smelter Registry — vetted ingredient catalog with CVE scanning (pip-audit), STRICT/WARNING enforcement, compliance badging on templates; blocks non-compliant builds at Foundry
- Package Repository Mirroring — local PyPI (pypiserver) + APT (Caddy) sidecars, auto-sync on ingredient add, air-gapped manual upload, pip.conf/sources.list injection; fail-fast enforcement at build time
- Foundry Wizard UI — 5-step guided composition wizard (Identity → Base Image → Ingredients → Tools → Review), JSON editor for power users, full Smelter Registry integration for ingredient picking
- Smelt-Check + BOM + Lifecycle — post-build ephemeral validation containers, JSON Bill of Materials capture, package index for fleet-wide BOM search, image lifecycle (ACTIVE/DEPRECATED/REVOKED) enforced at enrollment and work-pull

---

## v8.0 mop-push CLI & Job Staging (Shipped: 2026-03-15)

**Phases completed:** 3 phases (17–19), 14 plans

**Key accomplishments:**
- OAuth Device Flow (RFC 8628) — MoP-native IdP, browser approval page, JWT issuance; no external IdP dependency
- mop-push CLI — login/push/create commands, Ed25519 signing locally, private key never transmitted; installable as SDK package
- Job lifecycle status (DRAFT/ACTIVE/DEPRECATED/REVOKED) — full state machine with REVOKED enforcement at dispatch
- Dashboard Staging view — inspect drafts, finalize scheduling, one-click Publish; operators review before jobs run
- OIDC v2 architecture doc — documents future external IdP integration path

---

