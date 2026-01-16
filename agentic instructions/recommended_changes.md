# Recommended Changes: Security Hardening & Best Practices

This document outlines critical security findings and recommendations for the "Master of Puppets" codebase. It is intended to guide future agents and developers in securing the application.

## 🚨 Critical Security Issues (Immediate Action Required)

### 1. Hardcoded Credentials & Secrets
**Files Affected:** `agent_service/main.py`, `model_service/main.py`, `environment_service/node.py`, `dashboard/src/App.jsx`, `generate_certs.py`, Root directory files.

- **API Keys**: `API_KEY = "master-secret-key"` is hardcoded across all services and strictly exposed in the frontend (`App.jsx`).
- **Encryption Keys**: `ENCRYPTION_KEY` is hardcoded in `agent_service/main.py`. If this code is leaked, all historical secrets in the DB are compromised.
- **CA Password**: `ca_password.txt` containing the Certificate Authority password is present in the root directory.
- **Private Keys**: `node-*.key` and `certs/key.pem` are present in the source tree.

**Recommendation:**
- Remove all secrets from source code.
- Use **Environment Variables** (e.g., `os.getenv`) loaded from a `.env` file (which must be gitignored).
- Rotate all currently exposed keys immediately.
- Use a secret manager (e.g., HashiCorp Vault, AWS Secrets Manager) for production.

### 2. Remote Code Execution (RCE) Vulnerability
**Files Affected:** `dashboard/src/App.jsx`, `environment_service/node.py`

- The Dashboard allows users to submit arbitrary Python code (`script_content`) which is executed by the Node service (`exec(script_content)` equivalent via `subprocess`).
- Since the API Key is exposed in the Dashboard, **anyone** with access to the Dashboard can execute arbitrary code on the Node servers.

**Recommendation:**
- **Restrict Script Execution**: If arbitrary code execution is a feature, it MUST be sandboxed (e.g., Docker containers, gVisor, Firecracker microVMs).
- **Authentication**: Implement real user authentication (OIDC/OAuth2) for the Dashboard instead of a shared static API key.
- **Input Validation**: Validate `script_content` if possible, or use predefined tasks instead of raw script injection.

### 3. SSL/TLS Validation Disabled
**Files Affected:** `environment_service/node.py`, `model_service/main.py`

- Services use `verify=False` in `httpx` calls. This completely bypasses SSL certificate validation, making the system vulnerable to Man-in-the-Middle (MitM) attacks.
- Commnets indicate "Self-Signed" certs are the reason.

**Recommendation:**
- Distribute the **Root CA certificate** (`ca/certs/root_ca.crt`) to all services.
- Configure `httpx` to verify against this Root CA: `verify="/path/to/root_ca.crt"`.
- Ensure common names in certs match the service hostnames.

### 4. Exposed Private Keys in Root
**Files Affected:** `root_ca.key` (implied location), `node-*.key`

- Private keys for the CA and Nodes appear to be generated in the root or `certs/` directory and are not explicitly excluded in a comprehensive way (some might be, but `list_dir` showed `.key` files in root).

**Recommendation:**
- Move all certificates and keys to a dedicated `secrets/` directory.
- Add `*.key`, `*.pem`, `*.crt`, `*.p12` to `.gitignore`.

---

## 🔒 Hardening Recommendations (Medium Priority)

### 5. CORS Policy
**Files Affected:** `agent_service/main.py`, `model_service/main.py`

- `allow_origins=["*"]` allows any website to make requests to your local API.

**Recommendation:**
- Restrict `allow_origins` to specific domains (e.g., `http://localhost:5173` for the dashboard).

### 6. Hardcoded Absolute Paths
**Files Affected:** `agent_service/main.py`, `environment_service/node.py`

- Paths like `C:\Users\thoma\...` and `c:/Development/...` are hardcoded. This makes the code non-portable.

**Recommendation:**
- Use relative paths (e.g., `Path(__file__).parent / "certs"`).
- Use configuration variables for external tool paths (e.g., `STEP_EXE`).

### 7. Database Security
**Files Affected:** `agent_service/main.py`

- `sqlite3` is used. While fine for dev, ensure the file permissions on `jobs.db` are restricted.
- Ensure the `jobs.db` file is not in a web-accessible directory (it is currently in the root).

---

## 🛠 Refactoring & Code Quality

### 8. Dependency Management
- `environment_service/node.py` and `agent_service/main.py` duplicate logic (e.g., API Key constants, `verify=False`).
- **Recommendation**: Create a shared `common` library or package for shared constants, mTLS logic, and models.

### 9. Logging
- Secrets are "redacted" in some logs (`mask_secrets`), but raw payloads might be logged in exception handlers or debug prints.
- **Recommendation**: Use a structured logging library (like `structlog` or standard `logging` with filters) to ensure secrets are never written to stdout/files.

## Traceability & Next Steps

When reviewing this codebase, the next agent should:
1.  **Run `git rm --cached`** on all `.key` and password files.
2.  **Create a `.env.example`** file.
3.  **Refactor `agent_service`** to load config from env.
4.  **Implement proper mTLS** with the existing CA setup (enabling `verify=True`).
