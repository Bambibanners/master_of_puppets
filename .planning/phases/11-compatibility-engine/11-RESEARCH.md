# Phase 11: Compatibility Engine - Research

**Researched:** 2026-03-09
**Domain:** FastAPI backend (SQLAlchemy, Pydantic), React/TypeScript frontend (TanStack Query, Radix UI)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tool admin UI placement:**
- New "Tools" tab in the Foundry page, alongside the existing Templates and Blueprints tabs
- Editable table with columns: tool_id, OS family, validation_cmd, runtime_dependencies, active status
- Full CRUD: add new tool entries, edit existing ones, delete (soft-delete — marks inactive, never destroys)
- Soft-delete: if a tool entry is referenced by any existing blueprint, it is marked inactive (hidden from new blueprints) rather than hard-deleted; API returns info about which blueprints reference it
- Only active tool entries appear in the blueprint editor tool picker

**OS family on blueprints:**
- Explicit DEBIAN/ALPINE dropdown in the blueprint creation form — admin declares OS family; not auto-derived from base_os string
- Only DEBIAN and ALPINE for v1 (matches existing CapabilityMatrix seed data)
- OS family badge displayed on blueprint cards in the Foundry list views
- Backfill existing NULL blueprints to DEBIAN via migration (safe default — all current builds are Debian-based), then make os_family required for new blueprint creation
- Template creation validates only the runtime blueprint's OS family against tools; network blueprints are OS-agnostic and are not validated

**Runtime dependency representation:**
- `runtime_dependencies` stored as a JSON list of tool_ids (e.g. `["python-3.11"]`) on each CapabilityMatrix entry
- Dependencies are scoped per OS family implicitly — each CapabilityMatrix row is already (base_os_family × tool_id), so dependency tool_ids reference other entries within the same OS family
- Two-phase confirmation flow (API + UI):
  - When admin selects a tool with unsatisfied dependencies in the blueprint editor, a dialog prompts to confirm each missing dep individually before submission
  - At the API level: `POST /api/blueprints` returns 422 with a `deps_to_confirm` list if any tool has runtime dependencies not included in the blueprint's tool list
  - Caller resubmits with `confirmed_deps: ["python-3.11"]` to acknowledge and proceed — confirmed deps are auto-added to the blueprint
  - This applies to both UI and programmatic/CI callers

**OS compatibility validation (COMP-03):**
- Validation fires at blueprint creation time (`POST /api/blueprints`)
- Rejects if any selected tool_id has no active CapabilityMatrix entry for the blueprint's declared os_family
- Error response lists the offending tools explicitly: e.g. "Blueprint validation failed: tools [pwsh-7.4] have no CapabilityMatrix entry for ALPINE. Add ALPINE support for these tools or change the OS family."

**Foundry tool picker filtering (COMP-04):**
- Tools are filtered in real-time immediately as admin selects OS family in the blueprint creation form
- Only tools with an active CapabilityMatrix entry for the selected OS family are shown — incompatible tools are hidden entirely (not greyed out)
- Before OS family is selected, tool list shows a placeholder ("Select an OS family to see available tools")

### Claude's Discretion
- Exact table styling / column order for the Tools tab
- Modal vs inline form for adding/editing tool entries
- How to handle tools with deep dependency chains (transitive deps — detect and surface in one confirmation dialog or chain)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COMP-01 | Every tool in the CapabilityMatrix is tagged with an `os_family` (DEBIAN/ALPINE/etc.) | `os_family` already exists as `base_os_family` on the `CapabilityMatrix` DB model — it's already the primary key dimension of each row. The new `is_active` bool column makes this fully addressable. |
| COMP-02 | Tools can declare a required runtime dependency (e.g. Scapy requires Python 3.x) | New `runtime_dependencies TEXT` column (JSON list of tool_ids) on `capability_matrix` table. Migration v26 adds it with DEFAULT '[]'. API and model updated to expose it. |
| COMP-03 | Foundry API rejects blueprints where any tool's `os_family` doesn't match the selected base OS | Validation added to `POST /api/blueprints` — checks each tool_id in the definition against active CapabilityMatrix rows for the blueprint's declared `os_family`. Returns 422 with explicit list of offending tools. |
| COMP-04 | Foundry UI filters available tools in real-time based on selected base OS | `GET /api/capability-matrix?os_family=DEBIAN` query param added. `CreateBlueprintDialog.tsx` passes selected os_family to the query — tool list re-renders immediately on OS family change. |
</phase_requirements>

---

## Summary

Phase 11 is a metadata and enforcement layer on top of the existing Foundry system. The `CapabilityMatrix` table already stores tools keyed by `(base_os_family, tool_id)` — this is the correct schema for the OS-family dimension of COMP-01. The two missing columns are `runtime_dependencies` (TEXT, JSON list) and `is_active` (BOOLEAN, default TRUE). These require a migration file for existing deployed databases.

The `Blueprint` DB model already has an `os_family` column (Mapped[str]) that is currently never populated at creation time — it is NULL for all existing rows. The migration must backfill this to 'DEBIAN' before the API enforces non-null. The `BlueprintCreate` Pydantic model needs an `os_family` field added (required for RUNTIME blueprints, ignored for NETWORK). The frontend `CreateBlueprintDialog.tsx` needs an OS family dropdown added for RUNTIME type, and its tool-fetching query needs to pass `?os_family=<selected>` so only compatible tools are shown.

The dep-confirmation flow at the API is a two-pass POST: first call may return 422 with `deps_to_confirm`, second call includes `confirmed_deps` and proceeds. The frontend handles this with a confirmation dialog before resubmitting.

**Primary recommendation:** Implement in three waves — (1) DB migration + model/API changes for COMP-01/02/03, (2) frontend OS-filter wiring for COMP-04, (3) Tools tab CRUD in Foundry page.

---

## Standard Stack

### Core (already in use — no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy async | installed | ORM for CapabilityMatrix, Blueprint | Already used throughout |
| Pydantic v2 | installed | Request/response models | Already used throughout |
| FastAPI | installed | HTTP routes and validation | Already used throughout |
| TanStack Query | installed | React data fetching + cache invalidation | Already used in CreateBlueprintDialog |
| Radix UI / shadcn | installed | Select, Dialog, Badge, Table components | Already used in Foundry tab views |

### No New Dependencies Required

All functionality can be implemented with the existing stack. The dep-confirmation flow is pure API/logic — no new libraries.

---

## Architecture Patterns

### Recommended File Touch Map

```
puppeteer/
├── migration_v26.sql                          # NEW — adds is_active + runtime_dependencies to capability_matrix, backfills blueprints.os_family
├── agent_service/
│   ├── db.py                                  # MODIFY — add is_active, runtime_dependencies to CapabilityMatrix
│   ├── models.py                              # MODIFY — update CapabilityMatrixEntry, BlueprintCreate, BlueprintResponse
│   └── main.py                                # MODIFY — GET /api/capability-matrix (os_family filter), POST /api/blueprints (validation + dep flow), PATCH /api/capability-matrix/{id} (soft-delete)
└── dashboard/src/
    ├── views/
    │   └── Templates.tsx                      # MODIFY — add "Tools" as a 4th tab
    └── components/
        └── CreateBlueprintDialog.tsx          # MODIFY — OS family dropdown, filtered tool list, dep-confirm dialog
```

### Pattern 1: DB Model Column Addition

The `CapabilityMatrix` SQLAlchemy model gets two new columns. For new deployments, `create_all` picks them up. For existing deployed DBs, `migration_v26.sql` uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.

```python
# db.py — updated CapabilityMatrix model
class CapabilityMatrix(Base):
    __tablename__ = "capability_matrix"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    base_os_family: Mapped[str] = mapped_column(String)
    tool_id: Mapped[str] = mapped_column(String)
    injection_recipe: Mapped[str] = mapped_column(Text)
    validation_cmd: Mapped[str] = mapped_column(String)
    artifact_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("artifacts.id"), nullable=True)
    runtime_dependencies: Mapped[str] = mapped_column(Text, default="[]")   # NEW — JSON list of tool_ids
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)           # NEW — soft-delete flag
```

### Pattern 2: OS Family Filter on GET /api/capability-matrix

The existing route returns all rows. Add an optional `os_family` query parameter and an `active_only` default-true filter:

```python
# main.py
@app.get("/api/capability-matrix", response_model=List[CapabilityMatrixEntry])
async def get_capability_matrix(
    os_family: Optional[str] = None,
    current_user: User = Depends(require_permission("foundry:read")),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CapabilityMatrix).where(CapabilityMatrix.is_active == True)
    if os_family:
        stmt = stmt.where(CapabilityMatrix.base_os_family == os_family.upper())
    result = await db.execute(stmt)
    return result.scalars().all()
```

The Tools tab admin view calls the endpoint without the filter (to see all entries including inactive). The blueprint editor calls it with `?os_family=DEBIAN`.

### Pattern 3: Blueprint Creation Validation + Dep-Confirmation Flow

Two-pass POST on `POST /api/blueprints` for RUNTIME blueprints:

**Pass 1 — OS mismatch check (hard reject, 422):**
```python
# Collect tool_ids from definition
tool_ids = [t["id"] for t in definition.get("tools", [])]
declared_os = req.os_family.upper()  # e.g. "ALPINE"

# Check each tool has an active entry for the declared OS
stmt = select(CapabilityMatrix).where(
    CapabilityMatrix.is_active == True,
    CapabilityMatrix.base_os_family == declared_os,
    CapabilityMatrix.tool_id.in_(tool_ids)
)
result = await db.execute(stmt)
valid_tool_ids = {row.tool_id for row in result.scalars().all()}
incompatible = [t for t in tool_ids if t not in valid_tool_ids]
if incompatible:
    raise HTTPException(status_code=422, detail={
        "error": "os_mismatch",
        "message": f"Blueprint validation failed: tools {incompatible} have no CapabilityMatrix entry for {declared_os}.",
        "offending_tools": incompatible
    })
```

**Pass 2 — Runtime dependency check (soft reject, 422 with confirmation list):**
```python
# For each valid tool, load its runtime_dependencies
stmt = select(CapabilityMatrix).where(
    CapabilityMatrix.is_active == True,
    CapabilityMatrix.base_os_family == declared_os,
    CapabilityMatrix.tool_id.in_(tool_ids)
)
rows = (await db.execute(stmt)).scalars().all()

tool_set = set(tool_ids)
confirmed_deps = set(req.confirmed_deps or [])
missing_deps = []
for row in rows:
    deps = json.loads(row.runtime_dependencies or "[]")
    for dep in deps:
        if dep not in tool_set and dep not in confirmed_deps:
            missing_deps.append(dep)

if missing_deps:
    raise HTTPException(status_code=422, detail={
        "error": "deps_required",
        "message": "Some tools have unsatisfied runtime dependencies.",
        "deps_to_confirm": list(set(missing_deps))
    })

# Auto-add confirmed deps to the blueprint's tool list before saving
all_tools = tool_ids + [d for d in confirmed_deps if d not in tool_set]
definition["tools"] = [{"id": t, "version": "latest"} for t in all_tools]
```

### Pattern 4: Soft-Delete on PATCH /api/capability-matrix/{id}

Change the existing `PUT /api/capability-matrix/{id}` to `PATCH` for partial updates. Add a `DELETE` route that soft-deletes instead of hard-deletes:

```python
@app.delete("/api/capability-matrix/{id}")
async def delete_capability(id: int, ...):
    # Find blueprints referencing this tool_id + os_family
    cap = await db.get(CapabilityMatrix, id)
    # Check all blueprints for references
    bps = await db.execute(select(Blueprint))
    referencing = []
    for bp in bps.scalars().all():
        defn = json.loads(bp.definition)
        if cap.tool_id in [t["id"] for t in defn.get("tools", [])]:
            referencing.append({"id": bp.id, "name": bp.name})
    # Always soft-delete
    cap.is_active = False
    await db.commit()
    return {"status": "deactivated", "referencing_blueprints": referencing}
```

### Pattern 5: Frontend OS Family Wiring in CreateBlueprintDialog

The existing dialog fetches `GET /api/capability-matrix` once. Change to refetch when OS family changes:

```typescript
// Add os_family state for RUNTIME blueprints
const [osFamilySelection, setOsFamilySelection] = useState<'DEBIAN' | 'ALPINE' | ''>('');

// Query depends on osFamilySelection
const { data: matrix = [] } = useQuery({
    queryKey: ['capability-matrix', osFamilySelection],
    queryFn: async () => {
        if (!osFamilySelection) return [];
        const res = await authenticatedFetch(`/api/capability-matrix?os_family=${osFamilySelection}`);
        return await res.json();
    },
    enabled: !!osFamilySelection
});
```

Render a placeholder when `osFamilySelection` is empty:
```typescript
{!osFamilySelection ? (
    <p className="text-zinc-500 text-sm">Select an OS family to see available tools</p>
) : (
    // existing tool chip list
)}
```

### Pattern 6: Dep-Confirm Dialog in CreateBlueprintDialog

The `createMutation` must handle 422 responses with `deps_to_confirm`:

```typescript
const [pendingDeps, setPendingDeps] = useState<string[]>([]);
const [confirmedDeps, setConfirmedDeps] = useState<string[]>([]);

const createMutation = useMutation({
    mutationFn: async (opts?: { confirmed_deps?: string[] }) => {
        const body = { type, name, os_family: osFamilySelection, definition, confirmed_deps: opts?.confirmed_deps };
        const res = await authenticatedFetch('/api/blueprints', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (res.status === 422) {
            const err = await res.json();
            if (err.detail?.error === 'deps_required') {
                setPendingDeps(err.detail.deps_to_confirm);
                return null; // Hold — show dep dialog
            }
            throw new Error(err.detail?.message || 'Validation failed');
        }
        if (!res.ok) throw new Error('Failed to create blueprint');
        return await res.json();
    },
    onSuccess: (data) => {
        if (!data) return; // Waiting for dep confirmation
        queryClient.invalidateQueries({ queryKey: ['blueprints'] });
        onOpenChange(false);
        resetForm();
    }
});
```

### Anti-Patterns to Avoid

- **Hard-deleting CapabilityMatrix rows:** Existing blueprints reference tool_ids by name in their `definition` JSON. Hard delete would silently break those blueprints at build time. Always soft-delete.
- **Filtering tools in the frontend without the server:** The OS filter MUST be server-side. If new tool entries are added, the frontend cache must invalidate. Tie `queryKey` to `['capability-matrix', osFamilySelection]`.
- **Validating network blueprints against OS family:** Network blueprints have no tools — validation must only fire for `type == 'RUNTIME'`.
- **Checking `Blueprint.os_family` in foundry_service.py after migration:** The `foundry_service.py` currently derives `os_family` from `base_os` string (`"ALPINE" if "alpine" in base_os.lower() else "DEBIAN"`). After this phase, `rt_bp.os_family` should be used directly. The derived logic becomes a fallback for blueprints that somehow lack the field.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON list storage for runtime_dependencies | Custom serialization class | `json.loads()` / `json.dumps()` in Python; `@field_validator` in Pydantic | Pattern already established for `target_tags`, `capabilities` in existing models |
| Query parameter filtering | Custom filter DSL | FastAPI `Optional[str] = Query(None)` | Native FastAPI query param binding |
| Two-pass API confirmation | Websocket or long-poll | Standard 422 + resubmit pattern | Simple, CI/CD friendly — no special client needed |
| Tool reference checking for soft-delete | FK constraints | Query all blueprints and parse definition JSON | Blueprints store tools as JSON inside `definition`, not as FK rows — DB constraints can't help here |

**Key insight:** The `definition` field on Blueprint is a JSON blob, not normalized tables. All tool reference lookups must parse JSON in Python — this is already the established pattern in `foundry_service.py` and `main.py`.

---

## Common Pitfalls

### Pitfall 1: Blueprint.os_family Column Exists But Is Always NULL

**What goes wrong:** The `Blueprint` DB model already has `os_family: Mapped[str]` declared, but `create_blueprint` in `main.py` never sets it. The column exists in the schema for new DBs (via `create_all`) but has never been populated.

**Why it happens:** The column was added to the DB model but the route handler was not updated. Existing deployed DBs have the column with NULL values.

**How to avoid:** migration_v26.sql must `UPDATE blueprints SET os_family = 'DEBIAN' WHERE os_family IS NULL` before any NOT NULL constraint is added. The `BlueprintCreate` model must add `os_family: str` as a required field for `type == 'RUNTIME'` (validated via `@model_validator`). The `create_blueprint` route must write `req.os_family` to `new_bp.os_family`.

**Warning signs:** If validation is added before the backfill, all existing blueprint creation would fail. Run the migration first.

### Pitfall 2: Seed Data Missing is_active / runtime_dependencies

**What goes wrong:** The startup seed in `main.py` creates `CapabilityMatrix(...)` objects without `is_active` or `runtime_dependencies`. After the columns are added to the DB model, the seed will hit an error if `is_active` has no `server_default` defined OR if the SQLAlchemy default doesn't propagate correctly at seed time.

**How to avoid:** Add `server_default="true"` to the `is_active` mapped column and `server_default="[]"` to `runtime_dependencies` in `db.py`. The seed objects should also explicitly set these: `is_active=True, runtime_dependencies="[]"`. The secondary Alpine seed block (for existing DBs that are missing Alpine entries) must also set these fields.

**Warning signs:** `IntegrityError` or `OperationalError` at startup on existing DB if columns are added without defaults.

### Pitfall 3: Filtering Only Active Tools Breaks Admin Tools Tab

**What goes wrong:** The Tools tab admin view needs to see ALL entries including inactive ones (to manage them — reactivate, understand what is soft-deleted). If the `GET /api/capability-matrix` endpoint always filters `is_active == True`, the admin cannot see deactivated entries.

**How to avoid:** Add `include_inactive: bool = False` query parameter. The blueprint editor calls without it (defaults to active-only). The Tools tab admin view calls with `?include_inactive=true`.

### Pitfall 4: Dep-Confirm Resubmit Loses Original Form State

**What goes wrong:** The dep-confirmation dialog appears mid-flow. If the user cancels and resubmits, the form state (tools, packages, name) must be preserved. If the dialog dismisses and resets the form, UX is broken.

**How to avoid:** Keep all form state in `CreateBlueprintDialog` as existing `useState` hooks. The dep-confirmation is an overlay dialog — it does not close the parent dialog. Only `onSuccess` after a clean 200 calls `resetForm()` and `onOpenChange(false)`.

### Pitfall 5: Transitive Dependency Loop

**What goes wrong:** If tool A depends on tool B, and tool B depends on tool A, the dep-confirmation flow could loop or produce confusing behavior.

**How to avoid (Claude's Discretion):** Collect all `runtime_dependencies` for the initial tool_id set in one pass (not recursively). A tool that is itself in the confirmation list does not trigger another dep check pass. The API returns the full flat list of missing deps after one level of expansion. Deep transitive deps are deferred.

### Pitfall 6: os_family Case Sensitivity

**What goes wrong:** Frontend sends "debian" or "Debian", API expects "DEBIAN". String comparison fails silently.

**How to avoid:** Normalize to uppercase in the Pydantic model using `@field_validator`. In the query param handler, call `.upper()` on the incoming value. The seed data uses "DEBIAN" and "ALPINE" consistently.

---

## Code Examples

### Migration SQL (migration_v26.sql)

```sql
-- migration_v26.sql: Compatibility Engine — adds is_active + runtime_dependencies to capability_matrix,
-- adds os_family to blueprints, backfills DEBIAN default for existing rows.
-- Safe for existing deployments; new deployments use create_all.

-- Add is_active and runtime_dependencies to capability_matrix
ALTER TABLE capability_matrix ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE capability_matrix ADD COLUMN IF NOT EXISTS runtime_dependencies TEXT NOT NULL DEFAULT '[]';

-- Backfill blueprints.os_family for existing NULL rows (DEBIAN is the safe default — all current builds are Debian-based)
UPDATE blueprints SET os_family = 'DEBIAN' WHERE os_family IS NULL;
```

### Updated CapabilityMatrixEntry Pydantic Model

```python
class CapabilityMatrixEntry(BaseModel):
    id: Optional[int] = None
    base_os_family: str
    tool_id: str
    injection_recipe: str
    validation_cmd: str
    artifact_id: Optional[str] = None
    runtime_dependencies: List[str] = []   # NEW
    is_active: bool = True                  # NEW

    @field_validator('base_os_family', mode='before')
    @classmethod
    def normalize_os_family(cls, v: str) -> str:
        return v.upper() if isinstance(v, str) else v

    @field_validator('runtime_dependencies', mode='before')
    @classmethod
    def deserialize_deps(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return _json.loads(v)
            except Exception:
                return []
        return v

    class Config:
        from_attributes = True
```

### Updated BlueprintCreate Pydantic Model

```python
from pydantic import model_validator

class BlueprintCreate(BaseModel):
    type: str  # RUNTIME, NETWORK
    name: str
    definition: Dict
    os_family: Optional[str] = None          # NEW — required for RUNTIME, ignored for NETWORK
    confirmed_deps: Optional[List[str]] = None  # NEW — dep-confirmation resubmit

    @field_validator('os_family', mode='before')
    @classmethod
    def normalize_os_family(cls, v):
        return v.upper() if isinstance(v, str) else v

    @model_validator(mode='after')
    def validate_runtime_requires_os_family(self):
        if self.type == 'RUNTIME' and not self.os_family:
            raise ValueError("os_family is required for RUNTIME blueprints")
        return self
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os_family` derived from `base_os` string in foundry_service.py | `os_family` declared explicitly on Blueprint at creation | Phase 11 | `foundry_service.py` should use `rt_bp.os_family` instead of re-deriving; the old derivation logic becomes dead code |
| `DELETE /api/capability-matrix/{id}` hard-deletes | `DELETE /api/capability-matrix/{id}` soft-deletes (sets `is_active=False`) | Phase 11 | Existing `delete_capability` route must be replaced; a new `PATCH` replaces the existing `PUT` |
| `GET /api/capability-matrix` returns all rows (no filter) | `GET /api/capability-matrix?os_family=X&include_inactive=false` | Phase 11 | CreateBlueprintDialog must pass `os_family` param; Tools tab must pass `include_inactive=true` |

**Deprecated/outdated after this phase:**
- `os_family = "ALPINE" if "alpine" in base_os.lower() else "DEBIAN"` in `foundry_service.py` line 41: Replace with `rt_bp.os_family` (with fallback for safety).

---

## Open Questions

1. **PATCH vs PUT for capability-matrix updates**
   - What we know: The current route is `PUT /api/capability-matrix/{id}` (full replacement). The CONTEXT.md specifies PATCH in the integration points.
   - What's unclear: Whether to add a new `PATCH` route alongside the existing `PUT`, or rename the existing `PUT` to `PATCH`.
   - Recommendation: Rename the existing `PUT` to `PATCH` with a partial-update Pydantic model (all fields Optional). The Tools tab will use PATCH for in-place edits.

2. **Blueprint os_family on NETWORK blueprints**
   - What we know: CONTEXT.md says network blueprints are OS-agnostic and are not validated. os_family is required only for RUNTIME.
   - What's unclear: Should os_family be stored on NETWORK blueprints at all (as null)?
   - Recommendation: Store NULL on NETWORK blueprints. The `@model_validator` only enforces it for RUNTIME. The migration does not backfill network blueprints.

3. **Where os_family lives in the Blueprint definition JSON vs the DB column**
   - What we know: `Blueprint.os_family` DB column exists (currently always NULL). The `definition` JSON blob for RUNTIME blueprints does not currently include os_family.
   - Recommendation: Store os_family in the DB column only (not duplicated in definition JSON). `BlueprintResponse` must include `os_family`. The `definition` JSON is for tools/packages only.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (backend), vitest (frontend) |
| Config file | `puppeteer/pytest.ini` (or none — run from `puppeteer/` dir) |
| Quick run command | `cd puppeteer && pytest tests/test_compatibility_engine.py -x` |
| Full suite command | `cd puppeteer && pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COMP-01 | CapabilityMatrix row has base_os_family (DEBIAN/ALPINE) and is_active fields accessible via API | unit | `pytest tests/test_compatibility_engine.py::test_matrix_has_os_family -x` | ❌ Wave 0 |
| COMP-02 | CapabilityMatrix row stores runtime_dependencies as JSON list of tool_ids | unit | `pytest tests/test_compatibility_engine.py::test_matrix_runtime_deps -x` | ❌ Wave 0 |
| COMP-03 | POST /api/blueprints with ALPINE os_family + DEBIAN-only tool returns 422 with offending_tools | unit | `pytest tests/test_compatibility_engine.py::test_blueprint_os_mismatch_rejected -x` | ❌ Wave 0 |
| COMP-03 | POST /api/blueprints with dep missing returns 422 with deps_to_confirm; resubmit with confirmed_deps succeeds | unit | `pytest tests/test_compatibility_engine.py::test_blueprint_dep_confirmation_flow -x` | ❌ Wave 0 |
| COMP-04 | GET /api/capability-matrix?os_family=ALPINE returns only ALPINE rows | unit | `pytest tests/test_compatibility_engine.py::test_matrix_os_family_filter -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd puppeteer && pytest tests/test_compatibility_engine.py -x`
- **Per wave merge:** `cd puppeteer && pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `puppeteer/tests/test_compatibility_engine.py` — covers COMP-01 through COMP-04 (5 test functions)
- [ ] Framework install: None needed — pytest already in use

---

## Sources

### Primary (HIGH confidence)

- Direct code inspection of `puppeteer/agent_service/db.py` — `CapabilityMatrix`, `Blueprint`, existing column layout
- Direct code inspection of `puppeteer/agent_service/main.py` — existing `create_blueprint`, `get_capability_matrix`, `create_capability`, `update_capability`, `delete_capability` route implementations
- Direct code inspection of `puppeteer/agent_service/models.py` — `CapabilityMatrixEntry`, `BlueprintCreate`, `BlueprintResponse` Pydantic shapes
- Direct code inspection of `puppeteer/dashboard/src/components/CreateBlueprintDialog.tsx` — existing query patterns, form state, tool chip rendering
- Direct code inspection of `puppeteer/migration_v25.sql` — confirms migration pattern and highest existing migration number (v25)
- Direct code inspection of `puppeteer/agent_service/services/foundry_service.py` — confirms `os_family` derivation from `base_os` string (line 41), `CapabilityMatrix` query pattern used in `build_template`
- Direct inspection of `.planning/phases/11-compatibility-engine/11-CONTEXT.md` — locked design decisions

### Secondary (MEDIUM confidence)

- Established project pattern for JSON-string deserialization in Pydantic: `@field_validator('target_tags', mode='before')` on `JobDefinitionResponse` — same approach applies to `runtime_dependencies` and `CapabilityMatrixEntry`
- Established project pattern for soft-delete via `is_active` bool: `ServicePrincipal.is_active`, `Trigger.is_active` — same approach for `CapabilityMatrix.is_active`

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies, all patterns already established in codebase
- Architecture: HIGH — code is directly inspected, all integration points are concrete
- Pitfalls: HIGH — derived from actual code state (e.g. Blueprint.os_family is NULL, seed doesn't set is_active)
- Migration number: HIGH — migration_v25.sql is the highest; migration_v26.sql is the correct next file

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable domain — FastAPI + React, no fast-moving external dependencies)
