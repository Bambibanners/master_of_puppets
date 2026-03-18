"""
Phase 30: Runtime Attestation — Test Scaffold

Plan 30-01: Establishes passing RSA round-trip tests and stubs for Plans 30-02/30-03.

Test inventory:
  PASSING NOW  (Wave 1 — pure crypto, no application code needed):
    test_attestation_rsa_roundtrip      — sign/verify round trip using PKCS1v15+SHA256
    test_attestation_mutation_fails     — tampered bundle raises InvalidSignature
    test_bundle_deterministic           — sort_keys=True produces identical bytes regardless of insertion order
    test_cert_serial_matches            — cert_serial field in bundle matches cert.serial_number

  PASSING NOW  (Wave 1 — DB schema inspection):
    test_execution_record_has_attestation_columns  — enabled in Task 2 after columns added

  SKIPPED until Plan 30-02/30-03:
    test_revoked_cert_stores_failed     — orchestrator verification logic (Plan 03)
    test_attestation_export_endpoint    — GET /execution-records/{id}/attestation (Plan 03)
    test_attestation_export_missing     — 404 when no attestation stored (Plan 03)
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
# Plan 30-02/30-03 stubs — skipped until node-side signing is implemented
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Implemented in plan 30-03: orchestrator verification logic")
def test_revoked_cert_stores_failed():
    """When a node cert is revoked, report_result() should store attestation_verified='failed'.

    Stub — implemented in Plan 30-03.
    """
    assert False, "TODO: implement in plan 30-03"


@pytest.mark.skip(reason="Implemented in plan 30-03: GET /execution-records/{id}/attestation endpoint")
def test_attestation_export_endpoint():
    """GET /execution-records/{id}/attestation returns AttestationExportResponse with bundle and sig.

    Stub — implemented in Plan 30-03.
    """
    assert False, "TODO: implement in plan 30-03"


@pytest.mark.skip(reason="Implemented in plan 30-03: 404 on missing attestation")
def test_attestation_export_missing():
    """GET /execution-records/{id}/attestation returns 404 when no attestation stored.

    Stub — implemented in Plan 30-03.
    """
    assert False, "TODO: implement in plan 30-03"
