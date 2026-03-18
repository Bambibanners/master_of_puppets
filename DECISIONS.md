# Architecture Decision Records

This file records significant architectural and operational decisions for Axiom Orchestrator.

---

## ADR-001: /docs/ Public Access Deferred

**Date:** 2026-03-18
**Status:** Accepted
**Decided by:** Thomas (Phase 33 context session)

### Decision

`/docs/` remains behind the Cloudflare Access policy. No public-facing path
for the MkDocs documentation site is activated for v10.0.

### Rationale

- The security guide documents mTLS/token architecture details, root CA
  handling, and key management procedures. Premature public exposure creates
  operational risk before the CE community is established and before content
  can be reviewed for public-safe language.
- CF Access (`dev.master-of-puppets.work`) is already in place and functional.
  The marginal cost of keeping it enabled is zero.
- Public documentation access is a growth-stage concern. v10.0 is a
  commercial launch milestone targeting known enterprise buyers who can be
  granted CF Access service tokens.

### CF Access Reference

- Tunnel ID: `27bf990f-4380-41ea-9495-6a1cda5fe2d7`
- Policy: `dev.master-of-puppets.work` enforces CF Access service token
- Service token expiry: 2027-03-04 (renew before this date)

### Review Trigger

Revisit this decision when:
- CE community onboarding begins (first external contributor or public install
  announcement), OR
- The first external contributor pull request is received, OR
- The service token is approaching expiry (2027-03-04) and a renewal decision
  is required.
