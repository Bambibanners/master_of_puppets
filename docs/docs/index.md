# Master of Puppets

**Master of Puppets** is a self-hosted orchestration platform for managing distributed agent nodes — deploy jobs, schedule tasks, and monitor your fleet from a central control plane.

## What it does

- **Node management** — Puppet nodes self-enroll via mTLS and poll for work. No inbound firewall rules needed.
- **Job dispatch** — Submit signed Python scripts to nodes matched by capability tags and resource limits.
- **Scheduled jobs** — Cron-based job definitions with APScheduler, scoped to node capability sets.
- **Foundry** — Build custom node images from runtime and network blueprints via the dashboard.
- **RBAC** — Three roles (`admin`, `operator`, `viewer`) with per-permission grants, service principals, and API keys.
- **Audit log** — All security-relevant actions logged and queryable from the dashboard.

## Architecture overview

```
Puppeteer (Control Plane)  ←── mTLS ──→  Puppet Nodes
  ├── Agent Service (8001)                  └── Polls /work/pull every N sec
  ├── Model Service (8000)                      Executes jobs, reports results
  ├── PostgreSQL
  └── React Dashboard
```

Nodes initiate all connections to the control plane — the **pull model** means no inbound ports need to be open on your nodes.

## Getting started

| Goal | Where to go |
|------|-------------|
| Run the stack locally or in production | [Setup & Deployment](developer/setup-deployment.md) |
| Understand the system internals | [Architecture](developer/architecture.md) |
| Contribute code or run tests | [Contributing](developer/contributing.md) |
| Explore the REST API | [API Reference](api-reference/index.md) |
