# Audit Log

The audit log records all security-relevant actions in Master of Puppets with a username, timestamp, action type, and optional resource context.

---

## Accessing the Audit Log

**Dashboard:** Navigate to **Audit Log** in the sidebar. Displays entries in reverse chronological order with username, action, resource ID, and timestamp.

**API:**

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  https://<HOST>/admin/audit-log
```

Requires `users:write` permission (admin-only by default).

---

## Log Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Auto-incrementing row ID |
| `timestamp` | datetime | UTC timestamp of the action |
| `username` | string | Human user (`alice`), service principal (`sp:ci-pipeline`), or `"scheduler"` for scheduled jobs |
| `action` | string | Event type — see inventory below |
| `resource_id` | string or null | ID of the affected resource (node UUID, job ID, template name, etc.) |
| `detail` | JSON or null | Additional context specific to the action type |

---

## Event Inventory

Complete list of all audit actions, grouped by category.

### Authentication

| Action | Triggered by |
|--------|-------------|
| `device_flow:token_issued` | CLI successfully completes device flow login |
| `device_flow:approved` | Admin approves a device flow request |
| `device_flow:denied` | Admin denies a device flow request |

### User Management

| Action | Triggered by |
|--------|-------------|
| `user:create` | Admin creates a new user |
| `user:delete` | Admin deletes a user |
| `user:role_change` | Admin changes a user's role |
| `user:password_changed` | User changes their own password |
| `user:password_reset` | Admin resets a user's password |
| `user:signing_key_created` | User uploads an Ed25519 signing key |
| `user:signing_key_deleted` | User or admin deletes a signing key |
| `user:api_key_created` | User creates an API key |
| `user:api_key_revoked` | User or admin revokes an API key |

### Service Principals

| Action | Triggered by |
|--------|-------------|
| `sp:created` | Admin creates a service principal |
| `sp:updated` | Admin updates a service principal (name, role, or expiry) |
| `sp:deleted` | Admin deletes a service principal |
| `sp:secret_rotated` | Admin rotates a service principal secret |

### Permissions

| Action | Triggered by |
|--------|-------------|
| `permission:grant` | Admin grants a permission to a role |
| `permission:revoke` | Admin revokes a permission from a role |

### Jobs

| Action | Triggered by |
|--------|-------------|
| `job:cancel` | Operator cancels a running job |
| `job:retry` | Operator retries a failed job |
| `job:pushed` | `mop-push` submits a job to staging |
| `job:cron_skip` | Scheduler skips a cron fire (previous instance still running) |
| `job:draft_skip` | Scheduler skips a job still in DRAFT status |
| `job:revoked_skip` | Scheduler skips a REVOKED job definition |
| `job:deprecated_skip` | Scheduler skips a DEPRECATED job definition |

### Nodes

| Action | Triggered by |
|--------|-------------|
| `node:delete` | Admin deletes a node record |
| `node:revoke` | Admin revokes a node's certificate |
| `node:clear_tamper` | Admin clears a node's tamper flag |
| `node:upgrade_staged` | Admin stages a node upgrade |
| `node:reinstate` | Admin reinstates a previously revoked node |

### Foundry

| Action | Triggered by |
|--------|-------------|
| `template:build` | Operator triggers a Foundry image build |
| `template:delete` | Operator deletes a template |
| `blueprint:delete` | Operator deletes a blueprint |
| `foundry:image_status_updated` | Admin updates an image lifecycle status |

### Signing Keys

| Action | Triggered by |
|--------|-------------|
| `key:upload` | Operator uploads a signing public key |
| `signature:delete` | Operator deletes a signing key |

### Smelter and Mirror

| Action | Triggered by |
|--------|-------------|
| `smelter:ingredient_added` | Admin adds an approved ingredient |
| `smelter:ingredient_deactivated` | Admin deactivates an ingredient |
| `smelter:config_updated` | Admin updates Smelter configuration |
| `mirror:config_updated` | Admin updates mirror URLs |
| `smelter:package_uploaded` | Admin uploads a package to the mirror |
| `smelter:scan_triggered` | Admin triggers a CVE scan |

### System

| Action | Triggered by |
|--------|-------------|
| `base_image:marked_updated` | Admin marks the base image as updated |
| `signal:fire` | Admin fires a manual signal |

---

## Compliance Query Patterns

The following patterns address common compliance reporting requirements. All queries require `users:write` permission.

**All actions by a specific user**

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://<HOST>/admin/audit-log?username=alice"
```

Useful for user access reviews and offboarding audits.

**All service principal activity**

Filter by username prefix `sp:` — all service principal audit entries use `sp:<name>` as the username:

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://<HOST>/admin/audit-log?username=sp%3Aci-pipeline"
```

**All permission changes**

Filter by action `permission:grant` and `permission:revoke`. Review quarterly to detect permission creep — permissions granted temporarily that were never revoked.

**All node lifecycle events**

Filter by action prefix `node:` to get the complete lifecycle of all nodes (enrollment, revocation, reinstatement):

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://<HOST>/admin/audit-log?action_prefix=node%3A"
```

**All events for a specific resource**

Filter by `resource_id` (node UUID, job ID, template name) to see the complete event history of a single resource:

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://<HOST>/admin/audit-log?resource_id=<NODE_UUID>"
```

!!! tip
    For compliance windows (e.g., SOC 2 audit periods), the `timestamp` field in the JSON response is UTC ISO 8601. Export the full log to a SIEM or append it to a compliance evidence store at regular intervals to build an unbroken audit trail.

!!! warning
    The audit log is stored in the application database. For high-assurance deployments, export audit events to an immutable external store (e.g., S3 with object lock, or a SIEM) to prevent tampering by anyone with database access.

---

## Audit Attribution

Actions are attributed to the actor that initiated the request:

| Attribution format | Meaning |
|-------------------|---------|
| `alice` | Human user authenticated via JWT |
| `sp:ci-pipeline` | Service principal authenticated via client secret |
| `scheduler` | APScheduler triggered the action (cron job fires, skip events) |

This means the audit log can distinguish between a human operator cancelling a job and a service principal doing the same — even if they have identical permissions. For RBAC access review guidance using audit data, see [RBAC Hardening](rbac-hardening.md).
