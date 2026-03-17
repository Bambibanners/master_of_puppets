# RBAC Permission Reference

Complete reference for all permissions in Axiom, with default role assignments.

---

## Default Role Assignments

These are the default permissions assigned at first startup. Permissions can be customised per role through the dashboard — see the [RBAC guide](rbac.md).

| Permission | Description | admin | operator | viewer |
|---|---|:---:|:---:|:---:|
| `jobs:read` | View job queue and results | ✓ | ✓ | ✓ |
| `jobs:write` | Submit, cancel, and retry jobs | ✓ | ✓ | — |
| `nodes:read` | View node status and stats | ✓ | ✓ | ✓ |
| `nodes:write` | Enroll, revoke, and delete nodes | ✓ | ✓ | — |
| `definitions:read` | View scheduled job definitions | ✓ | ✓ | ✓ |
| `definitions:write` | Create, edit, and delete job definitions | ✓ | ✓ | — |
| `foundry:read` | View templates and blueprints | ✓ | ✓ | ✓ |
| `foundry:write` | Create, build, and delete templates/blueprints | ✓ | ✓ | — |
| `signatures:read` | View signing keys | ✓ | ✓ | ✓ |
| `signatures:write` | Upload and delete signing keys | ✓ | ✓ | — |
| `tokens:write` | Issue device flow tokens | ✓ | ✓ | — |
| `alerts:read` | View alerts | ✓ | ✓ | ✓ |
| `alerts:write` | Acknowledge and manage alerts | ✓ | ✓ | — |
| `webhooks:read` | View webhook configurations | ✓ | ✓ | — |
| `webhooks:write` | Create and delete webhooks | ✓ | ✓ | — |
| `users:write` | Manage users, roles, and permissions | ✓ | — | — |

The `admin` role bypasses all permission checks regardless of this table. `users:write` is the only permission not granted to `operator` by default; it governs user management and role configuration.

---

## Admin Role

Admin is not a permission set — it is an unconditional bypass. Any user with role `admin` can perform any action without a permission check. The table above does not constrain admin behaviour. Audit log entries for admin actions are recorded normally.

---

## Custom Permissions

Any permission can be granted to or revoked from any non-admin role via the dashboard (**Admin** → **Role Permissions**) or the API (`POST /admin/roles/{role}/permissions`, `DELETE /admin/roles/{role}/permissions/{permission}`). Changes take effect immediately for all new requests.

!!! warning
    Granting `users:write` to the `operator` role effectively gives every operator full control over user management, including the ability to create admin accounts. Treat `users:write` as an admin-tier permission.

For guidance on least-privilege configuration, see the [RBAC Hardening guide](../security/rbac-hardening.md).
