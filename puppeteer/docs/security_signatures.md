# Security Architecture: Signatures & Trust Chain

Master of Puppets v1.2 introduces a **Pass-Through Security Model** for job execution. This ensures that the code running on Nodes is byte-for-byte identical to the code authorized by the developer, preventing the Server from tampering with workloads.

## Core Hierarchy

1.  **Trust Anchor (Root CA)**: The internal Certificate Authority that issues mTLS certificates.
2.  **Code Signing Keys (Ed25519)**: Keys used by developers/pipelines to sign script content.
3.  **Signature Registry**: A whitelist of Authorized Public Keys stored on the Agent.

## Pass-Through Verification Flow

Puppeteer acts as a **Notary**, but not the final arbiter of trust for code content.

1.  **Authoring**: A developer writes a script and signs it with their Private Key (Ed25519).
2.  **Definition**: The Script + Signature is uploaded to Puppeteer.
    *   *Puppeteer validates the signature against the Registry to prevent bad uploads, but this is just a gatekeeper.*
3.  **Scheduling**: Puppeteer schedules the job.
4.  **Dispatch**: When the job triggers, Puppeteer sends the **Original Script** + **Original Signature** + **Key ID** to the Puppet.
5.  **Execution (Puppet-Side)**:
    *   The Puppet receives the payload.
    *   The Puppet fetches the Public Key from Puppeteer (via secure mTLS endpoint `/api/verification-key` or similar, or local cache).
    *   **CRITICAL**: The Puppet cryptographically verifies `Ed25519_Verify(Unmodified_Script, Signature, Public_Key)`.
    *   If valid, the script executes. If invalid, it is rejected immediately.

## Why this matters?

Even if the Agent Database is compromised or an attacker gains Admin access to the Dashboard:
*   They **cannot** inject malicious code into existing jobs without invalidating the signature.
*   They **cannot** create new malicious jobs without possessing a Private Key that corresponds to a trusted Public Key.

## Key Management

*   **Public Keys**: Uploaded to the Agent via Dashboard or API.
*   **Private Keys**: Kept offline or in secure CI/CD secrets. NEVER sent to the Server.
