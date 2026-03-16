# Master of Puppets (MoP)

[![Status](https://img.shields.io/badge/Status-Production--Ready-success.svg)](#)
[![Security](https://img.shields.io/badge/Security-Zero--Trust-blue.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#)

**Master of Puppets (MoP)** is a high-performance, enterprise-grade orchestration framework designed for secure and observable task execution across distributed environments. Built with a **Zero-Trust** architecture, MoP ensures that every component is mutually authenticated and every workload is cryptographically verified.

## 🚀 Key Value Propositions

*   **Zero-Trust Security**: Mutual TLS (mTLS) by default for all Control Plane <-> Node communications.
*   **Pull-Based Execution**: Nodes (Puppets) proactively poll for work, eliminating the need for inbound firewall rules on execution targets.
*   **Cryptographic Integrity**: All jobs must be signed using Ed25519 keys, ensuring only authorized workloads are executed.
*   **Enterprise Observability**: Real-time telemetry, job status tracking, and node health monitoring via a modern React Dashboard.
*   **Stateless Scaling**: Execution nodes are stateless and ephemeral, designed to run in isolated container environments (Podman/Docker).

---

## 🏗 Architecture Overview

MoP is comprised of three primary pillars:

### 1. The Puppeteer (Control Plane)
The central nervous system of the platform.
*   **API Gateway**: FastAPI-based RESTful API with OIDC/OAuth2 integration.
*   **PKI Authority**: Manages node enrollment, CSR signing, and certificate rotation.
*   **Scheduler**: Advanced recurring task engine and job queue management.
*   **Persistence**: PostgreSQL for robust state and history management.

### 2. The Puppet (Execution Node)
Lightweight, secure worker agents.
*   **Secure Enrollment**: Bootstraps trust via one-time join tokens and automated CSR generation.
*   **Workload Isolation**: Executes tasks in isolated subprocesses or containerized environments.
*   **Proactive Reporting**: Continuous heartbeats including system metrics and job lifecycle events.

### 3. MoP SDK & CLI
The primary interface for developers and automated CI/CD pipelines.
*   **Device Flow Auth**: Modern OAuth2 Device Flow for secure CLI authentication.
*   **Job Signing**: Built-in utilities for signing scripts before deployment.
*   **Programmatic Access**: Full Python SDK for integrating MoP into existing platforms.

---

## 🚦 Getting Started

### Prerequisites
*   Python 3.12+
*   Docker & Docker Compose (for full stack deployment)
*   Node.js & npm (for dashboard development)

### Deployment (Quick Start)
Deploy the full control plane stack using Docker Compose:

```bash
docker compose -f puppeteer/compose.server.yaml up -d
```

### CLI Installation & Authentication
Install the MoP SDK and authenticate via the CLI:

```bash
# Install SDK
pip install ./mop_sdk

# Login via Device Flow
mop-push login --url https://mop.your-enterprise.com
```

### Deploying a Job
1.  **Generate Keys**: Create an Ed25519 key pair for job signing.
2.  **Push Job**:
    ```bash
    mop-push job create \
      --name "System-Cleanup" \
      --script "./scripts/cleanup.py" \
      --key "./keys/private.pem" \
      --key-id "ops-team-01" \
      --cron "0 0 * * *" \
      --tags "prod,linux"
    ```

---

## 🛡 Security & Compliance

MoP is designed to meet the rigorous security requirements of modern enterprise environments:
*   **Identity**: Each node has a unique X.509 identity.
*   **Encryption**: All data in transit is encrypted via TLS 1.3.
*   **Provenance**: Strict Ed25519 signature verification prevents unauthorized code execution.
*   **Auditability**: Comprehensive logging of all API access, job submissions, and execution results.

For detailed security documentation, see [docs/security.md](docs/security.md).

---

## 📖 Documentation
*   [Architecture Deep Dive](docs/architecture.md)
*   [Deployment Guide](docs/deployment_guide.md)
*   [API Reference](docs/API_REFERENCE.md)
*   [User Guide](docs/UserGuide.md)

---
*© 2026 Master of Puppets Project. Built for security, scale, and simplicity.*
