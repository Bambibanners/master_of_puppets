---
phase: 25-runbooks-troubleshooting
verified: 2026-03-17T17:00:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
---

# Phase 25: Runbooks & Troubleshooting Verification Report

**Phase Goal:** Deliver four production-quality troubleshooting runbooks (nodes, jobs, foundry, faq) integrated into the MkDocs documentation site, giving operators a structured reference for diagnosing and resolving the most common failure patterns.
**Verified:** 2026-03-17T17:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | mkdocs.yml has all five Runbooks nav entries (index + nodes, jobs, foundry, faq) | VERIFIED | Lines 46–51 of docs/mkdocs.yml confirmed: Overview, Node Troubleshooting, Job Execution, Foundry, FAQ all present |
| 2 | An operator with a broken node can match symptom to runbook section and follow numbered recovery steps | VERIFIED | nodes.md: 296 lines, 10 H3 symptoms across 3 H2 clusters, 11 "Recovery steps" sections, 10 "Verify it worked" sections, 10 escalation notes |
| 3 | Job failures (stuck, rejected, dead-lettered) are diagnosable from a dashboard status alone | VERIFIED | jobs.md: 258 lines, 10 H3 symptoms, covers PENDING/BLOCKED/CANCELLED/DEAD_LETTER/ZOMBIE_REAPED/SECURITY_REJECTED with exact log strings from node.py and job_service.py |
| 4 | Foundry build failures (docker build, Smelt-Check, registry push) are documented with root causes and recovery steps | VERIFIED | foundry.md: 193 lines, 8 H3 symptoms across 3 H2 clusters, verbatim log strings from foundry_service.py in code blocks |
| 5 | All four required gotchas and three required how-tos are in the FAQ | VERIFIED | faq.md: 133 lines, 10 H3 entries — blueprint dict format, EXECUTION_MODE=direct, JOIN_TOKEN structure, ADMIN_PASSWORD seed-only, node reset, UTC timezone, Ed25519 cannot be bypassed (danger admonition confirmed) |
| 6 | The Runbooks overview page links to all four runbook pages | VERIFIED | docs/docs/runbooks/index.md: real overview page with a guide table linking nodes.md, jobs.md, foundry.md, faq.md |
| 7 | Exact log strings from source code appear verbatim in runbooks so operators can search-match their terminal output | VERIFIED | nodes.md: enrollment failure strings, SSL strings, Token payload missing; jobs.md: Signature Verification FAILED, Verification Key missing, exhausted all N retries; foundry.md: Build Failed, Smelt-Check FAILED, environment_service not found — all confirmed in code blocks |
| 8 | Cross-links use confirmed anchors (not guessed slugs) | VERIFIED | nodes.md links to ../security/mtls.md#certificate-rotation and faq.md; jobs.md links to ../feature-guides/mop-push.md#ed25519-key-setup and faq.md; foundry.md links to ../feature-guides/foundry.md#blueprints, #smelter, #image-lifecycle, and ../security/air-gap.md; faq.md links to mop-push.md, mtls.md, foundry.md, job-scheduling.md |
| 9 | The zombie reaper is documented as the effective operator-visible job timeout (not the 30-second subprocess path) | VERIFIED | jobs.md "Timeout Patterns" cluster explicitly documents zombie_timeout_minutes (default 30 min, configurable) as the operator-visible timeout; the direct subprocess path is not mentioned |
| 10 | The FAQ Ed25519 signing entry explicitly states verification cannot be bypassed | VERIFIED | faq.md contains `!!! danger` admonition: "There is no configuration flag, environment variable, or API option to disable signature verification. This is a security invariant." |
| 11 | The FAQ ADMIN_PASSWORD entry directs to the dashboard, not .env editing | VERIFIED | faq.md entry explains env var is read once at first startup; instructs operator to use Admin → Users → admin → Reset Password |
| 12 | All four plan commits exist in git history | VERIFIED | Confirmed: b89702b (mkdocs.yml nav), b7a2df7 (stubs + index), b493585 (foundry.md), 22a5beb (faq.md) |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/mkdocs.yml` | Nav entries for all five runbook pages | VERIFIED | Lines 46–51: five Runbooks nav entries present |
| `docs/docs/runbooks/index.md` | Overview page with guide table (min 15 lines) | VERIFIED | 19 lines; real content — symptom-first intro, guide table with 4 links, architecture cross-link |
| `docs/docs/runbooks/nodes.md` | Full node runbook, min 120 lines, contains `## Quick Reference` | VERIFIED | 296 lines; Quick Reference table with 10 anchors; 3 H2 clusters (Enrollment Failures, Heartbeat Loss, Certificate Errors) |
| `docs/docs/runbooks/jobs.md` | Full job runbook, min 120 lines, contains `## Quick Reference` | VERIFIED | 258 lines; Quick Reference table with 10 anchors; 3 H2 clusters (Dispatch Failures, Signing Errors, Timeout Patterns) |
| `docs/docs/runbooks/foundry.md` | Foundry runbook, min 80 lines, contains `## Quick Reference` | VERIFIED | 193 lines; Quick Reference table with 8 anchors; 3 H2 clusters (Build Failures, Smelt-Check Failures, Registry Issues) |
| `docs/docs/runbooks/faq.md` | FAQ, min 80 lines, contains `ADMIN_PASSWORD` | VERIFIED | 133 lines; 10 H3 entries; ADMIN_PASSWORD entry present with warning admonition |

---

### Key Link Verification

| From | To | Via | Pattern | Status | Details |
|------|----|-----|---------|--------|---------|
| nodes.md | security/mtls.md | cross-link | `../security/mtls.md#certificate-rotation` | VERIFIED | Found: "mTLS guide → Certificate Rotation" |
| nodes.md | security/mtls.md | cross-link | `../security/mtls.md#certificate-revocation` | VERIFIED | Found in Certificate Errors cluster |
| nodes.md | security/mtls.md | cross-link | `../security/mtls.md#the-join_token` | VERIFIED | Found in SSL verification section |
| nodes.md | runbooks/faq.md | cross-link | `faq.md` | VERIFIED | Found: link to faq.md#why-does-my-node-appear-multiple-times |
| jobs.md | feature-guides/mop-push.md | cross-link | `../feature-guides/mop-push.md#ed25519-key-setup` | VERIFIED | Found in 3 locations in Signing Errors cluster |
| jobs.md | runbooks/faq.md | cross-link | `faq.md` | VERIFIED | Found in See Also section |
| foundry.md | feature-guides/foundry.md | cross-link | `../feature-guides/foundry.md#blueprints` | VERIFIED | Found in Build Failures cluster |
| foundry.md | feature-guides/foundry.md | cross-link | `../feature-guides/foundry.md#smelter` | VERIFIED | Found in unapproved ingredients section |
| foundry.md | security/air-gap.md | cross-link | `../security/air-gap.md` | VERIFIED | Found in not-mirrored section |
| faq.md | feature-guides/mop-push.md | cross-link | `../feature-guides/mop-push.md` | VERIFIED | Found in Ed25519 signing entry |
| faq.md | security/mtls.md | cross-link | `../security/mtls.md#the-join_token` | VERIFIED | Found in JOIN_TOKEN gotcha entry |
| mkdocs.yml | docs/runbooks/nodes.md | nav entry | `runbooks/nodes.md` | VERIFIED | Line 48 confirmed |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| RUN-01 | 25-01, 25-02 | Node troubleshooting guide covers enrollment failures, heartbeat loss, and cert errors (symptom-first) | SATISFIED | nodes.md: 296 lines, 10 H3 symptoms, 3 H2 clusters map exactly to the three stated failure areas |
| RUN-02 | 25-01, 25-03 | Job execution troubleshooting covers dispatch failures, signing errors, and timeout patterns | SATISFIED | jobs.md: 258 lines, 3 H2 clusters (Dispatch Failures, Signing Errors, Timeout Patterns) matching the requirement exactly |
| RUN-03 | 25-01, 25-04 | Foundry troubleshooting covers build failures, Smelt-Check failures, and registry issues | SATISFIED | foundry.md: 193 lines, 3 H2 clusters (Build Failures, Smelt-Check Failures, Registry Issues) matching exactly |
| RUN-04 | 25-01, 25-04 | FAQ addresses the top operator questions (common misconfigurations, gotchas) | SATISFIED | faq.md: 10 H3 entries including all 4 required gotchas and all 3 required how-tos |

No orphaned requirements detected. REQUIREMENTS.md shows all four RUN-0x IDs marked complete and assigned to Phase 25.

---

### Anti-Patterns Found

No anti-patterns detected. Specific checks performed:

- No "Content coming soon" stub text remains in any of the four runbook files (Wave 1 stubs were fully replaced by Wave 2 plans)
- No empty implementations or placeholder returns
- No TODO/FIXME/HACK/PLACEHOLDER comments in any runbook file
- nodes.md healthy startup reference is a real content block (tip admonition with actual log lines), not a placeholder

---

### Human Verification Required

#### 1. MkDocs Strict-Mode Build

**Test:** Run `docker compose -f puppeteer/compose.server.yaml build docs`
**Expected:** BUILD successful with no warnings; all five Runbooks nav entries resolve to existing files
**Why human:** Docker daemon required; cannot run in this verification context. All four SUMMARY files report the build passed, and the nav entries and files confirmed by file checks, but live Docker build confirmation is the definitive test.

#### 2. Anchor Slug Resolution in Rendered MkDocs

**Test:** Browse the rendered docs to `/docs/runbooks/nodes/` and click each Quick Reference jump link
**Expected:** Each link scrolls to the corresponding H3 section
**Why human:** MkDocs anchor slug generation from H3 headers (especially those with special characters like `403`, `TAMPERED`, backticks stripped) cannot be verified without rendering. Plans noted the deliberate avoidance of backtick-wrapped H3 headers to ensure reliable slugs, but confirmation requires a browser.

#### 3. Cross-link Target Existence

**Test:** Browse each cross-link in the runbooks (e.g., `../security/mtls.md#certificate-rotation`, `../feature-guides/mop-push.md#ed25519-key-setup`, `../feature-guides/foundry.md#blueprints`)
**Expected:** All links resolve to the correct section in the target page without 404
**Why human:** Target files exist (confirmed in Phase 24), and anchors were verified against Phase 24 research, but rendered navigation requires a live docs instance.

---

### Summary

All four runbooks are substantive, production-quality documents — not stubs. The phase goal is fully achieved:

- **Structure:** All four runbooks follow the locked H2-cluster + H3-symptom pattern from the phase context. Every symptom section has a 2-sentence root cause, numbered recovery steps, a Verify step with expected output, and an escalation note.
- **Integration:** mkdocs.yml correctly registers all five Runbooks nav entries. The Wave 1 scaffolding (plan 25-01) and Wave 2 content plans (25-02 through 25-04) executed cleanly.
- **Cross-links:** All specified cross-links from plan frontmatter are present using confirmed anchor slugs from Phase 24 research.
- **Requirements:** All four RUN-0x requirements are fully satisfied. No orphaned requirements.
- **Commits:** All four task commits (b89702b, b7a2df7, b493585, 22a5beb) confirmed in git history.

Three human verification items remain (Docker build confirmation, anchor slug rendering, cross-link navigation) but these are confirmatory — automated checks give high confidence the phase goal was achieved.

---

_Verified: 2026-03-17T17:00:00Z_
_Verifier: Claude (gsd-verifier)_
