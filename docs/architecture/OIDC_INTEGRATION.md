# Architecture: OIDC & Identity Roadmap (v2)

## Current State: Internal OAuth 2.0 Device Flow
The MoP Control Plane currently implements a subset of RFC 8628 (OAuth 2.0 Device Authorization Grant) to facilitate CLI-based authentication without requiring users to transmit passwords or private keys.

### Device Flow Contract
1. **Authorization Request**: `POST /auth/device` returns `device_code`, `user_code`, and `verification_uri`.
2. **User Approval**: User navigates to the verification URI, logs into the dashboard (JWT-based), and approves the device code.
3. **Token Exchange**: CLI polls `POST /auth/device/token` and receives a standard JWT signed by the MoP internal `SECRET_KEY`.

## Roadmap: External OIDC Provider (v2)
The v2 roadmap transitions identity management to an external OpenID Connect (OIDC) provider (e.g., Keycloak, Okta, Auth0, or GitHub).

### Integration Path
- **Token Validation**: The MoP Control Plane will transition from internal JWT signing to verifying tokens issued by the OIDC provider's JWKS (JSON Web Key Set) endpoint.
- **Identity Mapping**: User roles will be derived from OIDC scopes/claims (e.g., `roles`, `groups`).
- **Standardized Device Flow**: The `mop-push` CLI will be updated to point its authorization request to the OIDC provider's native `/authorize` and `/token` endpoints.

## The Dual-Factor Integrity Model
MoP maintains security through two distinct verification layers:

1.  **Identity Layer (OIDC/JWT)**: Proves *who* is making the request. Ensures the operator is authorized to publish jobs.
2.  **Payload Layer (Ed25519)**: Proves *what* is being published. Ensures the script content matches the operator's local version and provides cryptographic non-repudiation.

### The API Contract
All job management endpoints (like `/api/jobs/push`) require both:
- `Authorization: Bearer <JWT>` (Identity)
- `X-MoP-Signature: <Ed25519-Signature>` (Payload Proof)

This model ensures that even if an OIDC session is compromised, the attacker cannot publish unauthorized scripts without the operator's local private key.
