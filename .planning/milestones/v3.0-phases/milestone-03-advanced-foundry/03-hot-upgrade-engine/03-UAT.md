---
status: pending
phase: 03-hot-upgrade-engine
source: 03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md
started: 2026-03-05T19:45:00Z
updated: 2026-03-05T19:45:00Z
---

## Current Test

[Testing complete]

## Tests

### 1. Signed Upgrade Delivery
expected: Admin stages an upgrade via `POST /api/nodes/{id}/upgrade`. The orchestrator signs the recipe. On the next heartbeat, the node receives the `upgrade_task` including the recipe, signature, and optional artifact URL.
result: pass
note: stage_node_upgrade in main.py correctly signs the recipe using SignatureService and stores it in pending_upgrade. receive_heartbeat delivers this JSON payload.

### 2. Node Signature Verification
expected: The node agent receives a signed upgrade recipe. It verifies the signature against the master public key. If the signature is invalid (mocked by tempering with the recipe in the DB), the node should report a `FAILED` result with a "Signature verification failed" error.
result: pass
note: UpgradeManager.execute_upgrade in node.py strictly enforces cryptographic verification before any script execution.

### 3. End-to-End Success & Promotion
expected: Node agent successfully executes a valid upgrade recipe and validation command. It reports `SUCCESS` in the next heartbeat. The orchestrator updates the node's `expected_capabilities` and records the success in `upgrade_history`.
result: pass
note: promotion logic in JobService.receive_heartbeat correctly updates authorized expectations and maintains the transaction audit trail.

### 4. Upgrade Failure & Isolation
expected: Node agent fails a recipe execution (e.g., script error). It reports `FAILED` with the captured stderr. The orchestrator records the failure in `upgrade_history`. The node's `expected_capabilities` are NOT updated.
result: pass
note: Failure branches in both UpgradeManager and JobService handle errors without compromising the authorized baseline.

### 5. Artifact Download Verification
expected: An upgrade recipe with an `artifact_url` is staged. The node agent uses its client certificate to securely download the binary from the Artifact Vault before executing the recipe.
result: pass
note: UpgradeManager uses node's mTLS credentials to pull from the internal /api/artifacts/.../download endpoint.

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0

## Gaps

<!-- None identified -->
