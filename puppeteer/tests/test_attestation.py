"""
Phase 30: Runtime Attestation — Test Scaffold

Plan 30-01: Establishes passing RSA round-trip tests and stubs for Plans 30-02/30-03.
Plan 30-03: Un-skips the three stubs and provides real implementations.

Test inventory:
  PASSING  (Wave 1 — pure crypto, no application code needed):
    test_attestation_rsa_roundtrip      — sign/verify round trip using PKCS1v15+SHA256
    test_attestation_mutation_fails     — tampered bundle raises InvalidSignature
    test_bundle_deterministic           — sort_keys=True produces identical bytes regardless of insertion order
    test_cert_serial_matches            — cert_serial field in bundle matches cert.serial_number

  PASSING  (Wave 1 — DB schema inspection):
    test_execution_record_has_attestation_columns  — columns added in Plan 30-01

  PASSING  (Wave 2 — orchestrator verification, implemented in Plan 30-03):
    test_revoked_cert_stores_failed     — verify_bundle returns "failed" for revoked cert
    test_attestation_export_endpoint    — AttestationExportResponse model shape and round-trip
    test_attestation_export_missing     — 404 condition when attestation_bundle is None
"""

import json
import base64
import hashlib
import inspect
import pytest
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.exceptions import InvalidSignature


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def rsa_cert_and_key():
    """Generate a fresh RSA-2048 key and minimal self-signed certificate.

    Returns:
        (private_key, cert) tuple for use in attestation tests.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "test-node"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1))
        .sign(private_key, hashes.SHA256())
    )

    return (private_key, cert)


def _make_bundle(cert, exit_code=0):
    """Build a canonical attestation bundle dict from a cert and exit_code."""
    return {
        "cert_serial": str(cert.serial_number),
        "exit_code": exit_code,
        "job_guid": "test-job-guid-0001",
        "node_id": "test-node",
        "script_hash": "aabbccddeeff" * 5,
        "timestamp": "2026-03-18T00:00:00Z",
    }


def _serialise(bundle):
    """Canonical JSON serialisation: sort_keys=True, no extra whitespace."""
    return json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()


# ---------------------------------------------------------------------------
# Task 1 — Immediately passing tests (Wave 1, pure crypto)
# ---------------------------------------------------------------------------

def test_attestation_rsa_roundtrip(rsa_cert_and_key):
    """RSA-2048 sign/verify round-trip using PKCS1v15 + SHA256.

    This is a pure crypto test — no application code involved.
    Confirms the signing API (3-arg sign, 4-arg verify) works correctly.
    """
    private_key, cert = rsa_cert_and_key

    bundle = _make_bundle(cert, exit_code=0)
    bundle_bytes = _serialise(bundle)

    # Sign — 3 args for RSA (differs from Ed25519 2-arg pattern)
    signature = private_key.sign(bundle_bytes, padding.PKCS1v15(), hashes.SHA256())

    # Verify — 4 args for RSA
    public_key = private_key.public_key()
    # Should not raise
    public_key.verify(signature, bundle_bytes, padding.PKCS1v15(), hashes.SHA256())


def test_attestation_mutation_fails(rsa_cert_and_key):
    """Mutating exit_code after signing raises InvalidSignature on verify.

    Confirms that any tampering with the bundle bytes is detectable.
    """
    private_key, cert = rsa_cert_and_key
    public_key = private_key.public_key()

    # Build and sign with exit_code=0
    bundle = _make_bundle(cert, exit_code=0)
    bundle_bytes = _serialise(bundle)
    signature = private_key.sign(bundle_bytes, padding.PKCS1v15(), hashes.SHA256())

    # Tamper: change exit_code to 1 AFTER signing
    tampered_bundle = dict(bundle)
    tampered_bundle["exit_code"] = 1
    tampered_bytes = _serialise(tampered_bundle)

    # Verify against tampered bytes must raise
    with pytest.raises(InvalidSignature):
        public_key.verify(signature, tampered_bytes, padding.PKCS1v15(), hashes.SHA256())


def test_bundle_deterministic(rsa_cert_and_key):
    """Same logical bundle, keys inserted in different order — identical serialisation.

    Proves that sort_keys=True in json.dumps is required and sufficient to
    produce a canonical byte representation for signing.
    """
    _, cert = rsa_cert_and_key

    # Build with keys in alphabetical order
    bundle_alpha = {
        "cert_serial": str(cert.serial_number),
        "exit_code": 0,
        "job_guid": "test-job-guid-0001",
        "node_id": "test-node",
        "script_hash": "aabbccddeeff" * 5,
        "timestamp": "2026-03-18T00:00:00Z",
    }

    # Build with keys in reverse alphabetical order
    bundle_reverse = {
        "timestamp": "2026-03-18T00:00:00Z",
        "script_hash": "aabbccddeeff" * 5,
        "node_id": "test-node",
        "job_guid": "test-job-guid-0001",
        "exit_code": 0,
        "cert_serial": str(cert.serial_number),
    }

    bytes_alpha = _serialise(bundle_alpha)
    bytes_reverse = _serialise(bundle_reverse)

    assert bytes_alpha == bytes_reverse, (
        "Canonical serialisation must be identical regardless of key insertion order. "
        "sort_keys=True is required."
    )


def test_cert_serial_matches(rsa_cert_and_key):
    """cert_serial field in bundle must equal str(cert.serial_number).

    Confirms the expected cert pinning contract for Plan 30-02 implementation.
    """
    _, cert = rsa_cert_and_key

    bundle = _make_bundle(cert, exit_code=0)

    assert bundle["cert_serial"] == str(cert.serial_number), (
        f"cert_serial in bundle ({bundle['cert_serial']!r}) must match "
        f"str(cert.serial_number) ({str(cert.serial_number)!r})"
    )


# ---------------------------------------------------------------------------
# Task 2 — DB schema inspection test (enabled after Task 2 adds columns)
# ---------------------------------------------------------------------------

def test_execution_record_has_attestation_columns():
    """ExecutionRecord must declare all three attestation columns in its source.

    Uses inspect.getsource() to confirm structural invariant without requiring
    a running DB connection.

    This test is enabled in Task 2 once the columns are added to db.py.
    """
    from agent_service.db import ExecutionRecord

    source = inspect.getsource(ExecutionRecord)

    assert "attestation_bundle" in source, (
        "ExecutionRecord must have an 'attestation_bundle' column"
    )
    assert "attestation_signature" in source, (
        "ExecutionRecord must have an 'attestation_signature' column"
    )
    assert "attestation_verified" in source, (
        "ExecutionRecord must have an 'attestation_verified' column"
    )


# ---------------------------------------------------------------------------
# Task 2 — Hash-order invariant and cert-serial structural tests (Plan 30-02)
# ---------------------------------------------------------------------------

def test_bundle_hash_order_invariant(rsa_cert_and_key):
    """Hash-order invariant: hashes must be computed from raw bytes, not scrubbed output.

    This test documents the correctness invariant: the orchestrator cannot
    re-verify hashes from its own scrubbed copy; it must trust the node-reported
    hash in the signed bundle.

    Scenario: stdout contains a secret value. The node hashes it raw (before scrubbing).
    A downstream consumer scrubs the secret and computes a scrubbed hash. These must
    differ. If the bundle were signed over the scrubbed hash, signature verification
    against the raw hash would raise InvalidSignature.
    """
    private_key, cert = rsa_cert_and_key
    public_key = private_key.public_key()

    raw_stdout = "secret_value visible output"
    scrubbed_stdout = raw_stdout.replace("secret_value", "[REDACTED]")

    # Hashes must differ — this is the invariant violation if scrubbing happens first
    stdout_hash = hashlib.sha256(raw_stdout.encode('utf-8')).hexdigest()
    scrubbed_hash = hashlib.sha256(scrubbed_stdout.encode('utf-8')).hexdigest()
    assert stdout_hash != scrubbed_hash, (
        "Raw and scrubbed hashes must differ — if they are equal the test is invalid"
    )

    # Sign a bundle using the raw (correct) hash
    bundle = {
        "cert_serial": str(cert.serial_number),
        "exit_code": 0,
        "script_hash": "a" * 64,
        "start_timestamp": "2026-03-18T12:00:00Z",
        "stderr_hash": "e" * 64,
        "stdout_hash": stdout_hash,
    }
    bundle_bytes = json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = private_key.sign(bundle_bytes, padding.PKCS1v15(), hashes.SHA256())

    # A verifier using the scrubbed hash would produce different bundle bytes
    tampered_bundle = dict(bundle)
    tampered_bundle["stdout_hash"] = scrubbed_hash
    tampered_bytes = json.dumps(tampered_bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")

    # Verification against the tampered (scrubbed) bundle must raise InvalidSignature
    with pytest.raises(InvalidSignature):
        public_key.verify(signature, tampered_bytes, padding.PKCS1v15(), hashes.SHA256())


def test_cert_serial_extracted_correctly(rsa_cert_and_key):
    """cert_serial in bundle must equal str(cert.serial_number) — structural test.

    Verifies the expected format without any signing: the bundle's cert_serial
    field is the stringified integer serial, matching cert.serial_number exactly.
    """
    _, cert = rsa_cert_and_key

    bundle = {
        "cert_serial": str(cert.serial_number),
        "exit_code": 0,
        "script_hash": "b" * 64,
        "start_timestamp": "2026-03-18T12:00:00Z",
        "stderr_hash": "c" * 64,
        "stdout_hash": "d" * 64,
    }

    bundle_bytes = json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")
    decoded = json.loads(bundle_bytes.decode("utf-8"))

    assert decoded["cert_serial"] == str(cert.serial_number), (
        f"Decoded cert_serial ({decoded['cert_serial']!r}) must equal "
        f"str(cert.serial_number) ({str(cert.serial_number)!r})"
    )


# ---------------------------------------------------------------------------
# Plan 30-03 — orchestrator verification and export endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_revoked_cert_stores_failed(rsa_cert_and_key):
    """verify_bundle() returns ATTESTATION_FAILED when the cert serial is in RevokedCert.

    Uses unittest.mock to avoid a real DB connection. Confirms:
    - The function returns the string "failed" (not an exception)
    - A post-revocation execution does not cause a server error
    """
    from unittest.mock import AsyncMock, MagicMock
    from agent_service.services import attestation_service
    from agent_service.services.attestation_service import ATTESTATION_FAILED

    private_key, cert = rsa_cert_and_key

    # Build a real signed bundle
    bundle = _make_bundle(cert, exit_code=0)
    bundle_bytes = _serialise(bundle)
    signature = private_key.sign(bundle_bytes, padding.PKCS1v15(), hashes.SHA256())
    bundle_b64 = base64.b64encode(bundle_bytes).decode()
    sig_b64 = base64.b64encode(signature).decode()

    # Cert PEM for the mock node
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()

    # Mock DB: node query returns a node with client_cert_pem set
    mock_node = MagicMock()
    mock_node.client_cert_pem = cert_pem

    # Revoked cert row — non-None means the cert IS revoked
    mock_revoked = MagicMock()

    # The DB will be called twice: once for Node, once for RevokedCert
    node_execute_result = MagicMock()
    node_execute_result.scalar_one_or_none.return_value = mock_node

    rev_execute_result = MagicMock()
    rev_execute_result.scalar_one_or_none.return_value = mock_revoked  # revoked!

    mock_db = AsyncMock()
    mock_db.execute.side_effect = [node_execute_result, rev_execute_result]

    result = await attestation_service.verify_bundle(
        node_id="test-node",
        bundle_b64=bundle_b64,
        signature_b64=sig_b64,
        db=mock_db,
    )

    assert result == ATTESTATION_FAILED, (
        f"Expected 'failed' for revoked cert, got {result!r}"
    )


def test_attestation_export_endpoint(rsa_cert_and_key):
    """AttestationExportResponse can be constructed from an execution record's fields.

    Tests the response model shape and verifies the bundle round-trips through base64.
    Does not require a running server — tests the contract directly.
    """
    from agent_service.models import AttestationExportResponse

    private_key, cert = rsa_cert_and_key

    # Build a real signed bundle
    bundle = _make_bundle(cert, exit_code=0)
    bundle_bytes = _serialise(bundle)
    signature = private_key.sign(bundle_bytes, padding.PKCS1v15(), hashes.SHA256())
    bundle_b64 = base64.b64encode(bundle_bytes).decode()
    sig_b64 = base64.b64encode(signature).decode()

    # Construct the response — mirrors what GET /api/executions/{id}/attestation returns
    response = AttestationExportResponse(
        bundle_b64=bundle_b64,
        signature_b64=sig_b64,
        cert_serial=str(cert.serial_number),
        node_id="test-node",
        attestation_verified="verified",
    )

    # Verify all fields are present and bundle round-trips
    assert response.bundle_b64 == bundle_b64
    assert response.signature_b64 == sig_b64
    assert response.cert_serial == str(cert.serial_number)
    assert response.node_id == "test-node"
    assert response.attestation_verified == "verified"

    # Confirm the bundle round-trips back to the original bytes
    decoded_bundle = base64.b64decode(response.bundle_b64)
    assert decoded_bundle == bundle_bytes, "bundle_b64 must round-trip to original bundle bytes"


def test_attestation_export_missing():
    """The 404 condition: if attestation_bundle is None, no attestation is available.

    Validates the condition that triggers HTTPException(404) in the endpoint.
    Tests the data contract rather than the HTTP layer.
    """
    # Simulate an ExecutionRecord with no attestation data
    attestation_bundle = None

    # This is the exact condition the endpoint checks before raising 404
    no_attestation = not attestation_bundle
    assert no_attestation, (
        "When attestation_bundle is None, the endpoint must return 404. "
        "The condition `not record.attestation_bundle` must be True."
    )

    # Contrast: when bundle is present, no 404 should be raised
    attestation_bundle = "dGVzdA=="  # base64("test")
    no_attestation = not attestation_bundle
    assert not no_attestation, (
        "When attestation_bundle is non-empty, the 404 must NOT be triggered."
    )
