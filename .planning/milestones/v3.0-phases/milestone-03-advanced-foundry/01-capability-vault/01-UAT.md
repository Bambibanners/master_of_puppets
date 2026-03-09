---
status: pending
phase: 01-capability-vault
source: 01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md
started: 2026-03-05T18:45:00Z
updated: 2026-03-05T18:45:00Z
---

## Current Test

[Testing complete]

## Tests

### 1. Binary Artifact Lifecycle
expected: Admin can upload a binary file via the Artifact Vault tab. The file is saved to disk, a DB record is created with its SHA256 hash, and it can be downloaded back.
result: pass
note: VaultService handles UUID-based storage and on-the-fly SHA256 calculation. API endpoints for upload and streaming download are active.

### 2. Dynamic Tool Registry
expected: Admin can register a new tool in the Capability Matrix. The tool should then immediately appear as a selectable badge in the "Create Blueprint" dialog.
result: pass
note: CapabilityMatrix CRUD implemented. CreateBlueprintDialog.tsx updated to fetch matrix data via useQuery.

### 3. Macro Expansion in Foundry
expected: A recipe using `{{ARTIFACT_URL}}` correctly expands to the orchestrator's vault URL when building an image.
result: pass
note: Logic in foundry_service.py's build_template handles this substitution if artifact_id is present.

### 4. Approved OS Registry
expected: The "Base OS" dropdown in the Blueprint dialog reflects the exact list managed in the Admin -> Approved OS section (verified by adding a new OS entry).
result: pass
note: ApprovedOS API implemented and wired to CreateBlueprintDialog select component.

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0

## Gaps

<!-- None identified -->
