# Automated Deployment Guide (OAuth2 / API)

This guide details how to use the **Puppeteer API** for automated deployments (CI/CD pipelines).

## Authentication (OAuth2)

The system uses standard OAuth2 Bearer Tokens (JWT). Your pipeline will first authenticate to obtain a `access_token`, which is valid for 24 hours.

### 1. Obtain Access Token

**Endpoint**: `POST /auth/login`
**Content-Type**: `application/x-www-form-urlencoded`

```bash
curl -X POST "https://<server>:8001/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -k \
     -d "username=admin&password=your_password"
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer",
  "role": "admin"
}
```

---

## Deployment Steps

### 2. Upload Trusted Signature (Optional)

If your pipeline rotates keys or needs to register a new signer (e.g., "Build Server 1"):

**Endpoint**: `POST /signatures`
**Header**: `Authorization: Bearer <access_token>`

```python
import requests

url = "https://localhost:8001/signatures"
headers = {"Authorization": f"Bearer {token}"}
payload = {
    "name": "CI/CD Pipeline Key",
    "public_key": "-----BEGIN PUBLIC KEY-----\n..."
}

resp = requests.post(url, json=payload, headers=headers, verify=False)
print(resp.json())
```

### 3. Deploy Scheduled Job

Deploy a signed job definition to the scheduler.

**Endpoint**: `POST /jobs/definitions`
**Header**: `Authorization: Bearer <access_token>`

**Required Fields**:
*   `name`: Unique Job Name.
*   `script_content`: The Python script to run.
*   `signature_id`: The UUID of the Public Key uploaded in Step 2.
*   `signature`: The **Base64 Encoded** signature of `script_content` (signed by the matching Private Key).
*   `schedule_cron`: Cron expression (e.g., `* * * * *`).

```python
import requests
import json

url = "https://localhost:8001/jobs/definitions"
headers = {"Authorization": f"Bearer {token}"}

payload = {
    "name": "Nightly Build Cleanup",
    "script_content": "print('Cleaning up artifacts...')",
    "signature": "<base64_signature_of_script>",
    "signature_id": "<uuid_of_public_key>",
    "schedule_cron": "0 2 * * *"  # 2 AM Daily
}

resp = requests.post(url, json=payload, headers=headers, verify=False)
print(resp.json())
```

## Security Best Practices for Automation

1.  **Dedicated User**: Create a specific user (e.g., `deployer`) with the `admin` or `operator` role instead of using the main `admin` account.
    *   *Currently, bootstrapping only creates `admin`. You can add new users via direct DB insertion or future User Management APIs.*
2.  **Secret Management**: Store the password and private signing key in your CI/CD secrets (e.g., GitHub Secrets, Vault).
3.  **TLS Verification**: In production, ensure you trust the Internal CA so you don't need `verify=False` / `-k`.
