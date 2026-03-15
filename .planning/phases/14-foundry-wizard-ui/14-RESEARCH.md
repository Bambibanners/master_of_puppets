# Phase 14: Foundry Wizard UI — Research

**Researched:** 2026-03-15
**Domain:** React multi-step wizard, Foundry blueprint composition UI
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Wizard Structure & Steps**
- Clone Support: Users can start fresh or clone from an existing blueprint template.
- Informative Base Selection: The image selection step will show "Last Updated" and "Compliance" metadata for approved OS images.
- Registry Transparency: Ingredient search results will display real-time `mirror_status` and `is_vulnerable` flags.
- Strict Compatibility: Only tools marked as compatible with the selected OS Family will be displayed in the Tool selection step.

**Interaction & "High Helpfulness" Logic**
- Auto-Dependency Injection: Selecting a Tool with `runtime_dependencies` will automatically add those packages to the ingredients list, accompanied by a UI notification.
- Permissive but Informed: Users can select `PENDING` or `VULNERABLE` ingredients, but the wizard will display explicit warnings about build failure risks and security vulnerabilities.
- Real-time Diffing: The final "Review" step will show a side-by-side JSON diff when editing or cloning, highlighting exactly what changed.

**Editor Co-existence & Governance**
- Wizard First: The primary "Create Blueprint" path is the Wizard.
- Advanced Escape Hatch: A "Raw JSON" editor is available under an "Advanced" toggle. Switching to it midway will convert the current wizard state into JSON.
- Friction-based Bypass: The advanced editor allows bypassing Smelter/Matrix validation, but only after an explicit confirmation/friction gate.
- Draft Persistence: The wizard supports saving partially completed configurations as "Drafts" for later resumption.

### Claude's Discretion
- Visual diff implementation: custom lightweight comparison view vs. `react-diff-viewer-continued`
- Internal state shape (Composition object structure)

### Deferred Ideas (OUT OF SCOPE)
- Alembic migrations or schema changes
- New backend routes beyond what Phase 11/12/13 provide
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WIZ-01 | User can create a valid blueprint without typing any JSON | 5-step wizard with structured inputs — BlueprintWizard.tsx implements this end-to-end |
| WIZ-02 | Selecting a tool automatically adds required PIP packages | `toggleTool` handler reads `runtime_dependencies` and merges them into `composition.packages.python` with deduplication |
| WIZ-03 | Vulnerable ingredients trigger visible security warnings | `is_vulnerable` badge rendered in Step 3 ingredient cards; `mirror_status` shown as "Sync Pending" amber badge |
</phase_requirements>

---

## Summary

Phase 14 implements a 5-step guided blueprint composition wizard that replaces the raw JSON blueprint editor in the Foundry view. All five implementation plans (14-01 through 14-05) have been completed, producing `BlueprintWizard.tsx` in `puppeteer/dashboard/src/components/foundry/`. The component is integrated into `Templates.tsx` as the primary "Create Blueprint" entry point.

The wizard's five steps are: (1) Identity — name, type, OS family, with clone support; (2) Base OS — filtered by OS family from `/api/approved-os`; (3) Ingredients — searchable package picker from `/api/smelter/ingredients` with mirror status and vulnerability badges; (4) Tools — OS-family-filtered picker from `/api/capability-matrix` with auto-dependency injection; (5) Review — summary panel plus JSON definition preview. An "Advanced (JSON)" toggle converts current state to raw JSON at any time.

The primary validation gap is unit test coverage for the wizard's core logic functions. No vitest tests exist yet for `BlueprintWizard.tsx` or its sibling `Templates.tsx`. The existing test pattern (vitest + React Testing Library + jsdom) is fully established at `puppeteer/dashboard/vitest.config.ts` and should be used directly.

**Primary recommendation:** Write vitest unit tests for `BlueprintWizard.tsx` covering the three WIZ requirements — the `blueprintToJson` serialiser, the `toggleTool` auto-injection branch, and the vulnerable-ingredient badge rendering path.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| vitest | already installed | Unit test runner for React components | Configured in vitest.config.ts; used by all existing dashboard tests |
| @testing-library/react | already installed | DOM rendering + querying in tests | Established by AddNodeModal.test.tsx and JobDefinitions.test.tsx |
| @testing-library/user-event | already installed | Simulates real user interaction | Present in node_modules, standard companion to @testing-library/react |
| @tanstack/react-query | already installed | Data fetching with caching | Used throughout wizard for approved-os, ingredients, capability-matrix |
| sonner (toast) | already installed | Dependency-injection toast notifications | Used in toggleTool; must be mocked in tests |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| jsdom | via vitest config | Simulates browser DOM | Required for all component tests — already configured |
| @testing-library/jest-dom | already installed | Custom matchers (toBeInTheDocument, etc.) | Already in setup.ts |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| vitest | jest | Vitest is already the project standard — no reason to switch |
| @testing-library/react | Playwright component tests | Playwright is heavier; unit tests with RTL are faster and already established |

**Installation:** No new packages required. All dependencies are present.

---

## Architecture Patterns

### Recommended Project Structure
```
puppeteer/dashboard/src/
├── components/
│   ├── foundry/
│   │   └── BlueprintWizard.tsx        # Implemented — 5-step wizard
│   └── __tests__/
│       ├── AddNodeModal.test.tsx       # Existing pattern to follow
│       └── BlueprintWizard.test.tsx   # MISSING — must be created
├── views/
│   ├── Templates.tsx                  # Wizard integrated here
│   └── __tests__/
│       └── JobDefinitions.test.tsx    # Existing pattern to follow
```

### Pattern 1: Component Mock Setup (established project pattern)
**What:** Mock `authenticatedFetch` with `vi.mock('../../auth', ...)` and mock `sonner` toast.
**When to use:** Any component test that calls the API or fires toasts.
**Example:**
```typescript
// Pattern from src/views/__tests__/JobDefinitions.test.tsx
const mockAuthFetch = vi.fn();
vi.mock('../../auth', () => ({
    authenticatedFetch: (...args: any[]) => mockAuthFetch(...args),
}));

// Also mock sonner for toast assertions
vi.mock('sonner', () => ({
    toast: {
        info: vi.fn(),
        success: vi.fn(),
        error: vi.fn(),
    },
}));
```

### Pattern 2: TanStack Query Test Wrapper
**What:** Wrap rendered components in a `QueryClientProvider` with a fresh `QueryClient` per test.
**When to use:** Any component that uses `useQuery` or `useMutation`.
**Example:**
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } }
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};
```

### Pattern 3: Pure Logic Extraction for Unit Testing
**What:** Extract `blueprintToJson` and `toggleTool` dependency-injection logic into pure functions importable outside the component.
**When to use:** When the logic under test doesn't require a rendered DOM.
**Example:**
```typescript
// blueprintUtils.ts (extract from BlueprintWizard.tsx)
export const blueprintToJson = (composition: Composition) => ({
    name: composition.name,
    type: composition.type,
    os_family: composition.os_family,
    definition: JSON.stringify({
        base_os: composition.base_os,
        packages: composition.packages,
        tools: composition.tools.map(tid => ({ id: tid, injection_recipe: '', validation_cmd: '' }))
    })
});
```

### Anti-Patterns to Avoid
- **Testing implementation details:** Don't assert on internal `useState` values — test rendered output and user interactions.
- **Not wrapping in QueryClientProvider:** Components with `useQuery` will throw without a provider — always wrap.
- **Mocking at module level without clearing:** Always call `vi.clearAllMocks()` in `beforeEach` (established pattern in existing tests).
- **Rendering without `open={true}`:** The wizard Dialog is conditional on the `open` prop — tests must pass `open={true}` to see content.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DOM querying in tests | Custom DOM traversal | @testing-library/react `screen` queries | Accessible-role queries are more robust than CSS selectors |
| Fake timers for async | Manual setTimeout chains | `waitFor()` from @testing-library/react | Built-in retry logic with configurable timeout |
| Query state reset between tests | Manual cache clearing | Fresh `QueryClient` per test | Prevents state leakage between test cases |
| Mock API responses | Fetch interception libs | `vi.fn()` on `authenticatedFetch` | Already established pattern; simpler than MSW for this codebase |

**Key insight:** The project has not adopted MSW (Mock Service Worker). The established pattern is mocking `authenticatedFetch` directly with `vi.fn()`. Follow this pattern — do not introduce MSW.

---

## Common Pitfalls

### Pitfall 1: Missing QueryClientProvider Wrapper
**What goes wrong:** `useQuery`/`useMutation` hooks throw "No QueryClient set" error in test environment.
**Why it happens:** TanStack Query requires context — the component uses `useQueryClient()` internally.
**How to avoid:** Always wrap the component under test in `QueryClientProvider` with `defaultOptions: { queries: { retry: false } }`.
**Warning signs:** Test error reads "No QueryClient set, use QueryClientProvider to set one."

### Pitfall 2: Dialog Content Not Rendered
**What goes wrong:** `screen.getByText('Foundry Wizard')` throws "Unable to find an element" even though the component is rendered.
**Why it happens:** Radix `Dialog` renders nothing to the DOM when `open={false}`.
**How to avoid:** Always pass `open={true}` when testing wizard content. Test the closed state separately.

### Pitfall 3: Sonner Toast Not Mocked
**What goes wrong:** Toast notifications fire into a void and warnings appear in test output.
**Why it happens:** `sonner` tries to interact with DOM features not present in jsdom.
**How to avoid:** Mock the `toast` object at the module level with `vi.mock('sonner', ...)`.

### Pitfall 4: Auto-Injection Side Effect Not Triggered
**What goes wrong:** Clicking a tool card doesn't update the packages state in the test.
**Why it happens:** `userEvent.click` needs to be awaited; `fireEvent.click` is synchronous but bypasses some React event handling.
**How to avoid:** Use `await userEvent.setup().click(toolCard)` or `fireEvent.click` followed by `await waitFor(...)` for state assertions.

### Pitfall 5: OS-Family Filter Silently Hides Tools
**What goes wrong:** Step 4 shows zero tools and test passes vacuously.
**Why it happens:** The matrix mock data must have `base_os_family` matching `composition.os_family` and `is_active: true` for tools to appear.
**How to avoid:** Seed mock data with explicit `{ tool_id: 'python', base_os_family: 'DEBIAN', is_active: true, runtime_dependencies: ['requests'] }`.

---

## Code Examples

### BlueprintWizard Test: Open/Close and Step 1 Render
```typescript
// Source: pattern from src/components/__tests__/AddNodeModal.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import BlueprintWizard from '../BlueprintWizard';

const mockAuthFetch = vi.fn();
vi.mock('../../../auth', () => ({
    authenticatedFetch: (...args: any[]) => mockAuthFetch(...args),
}));
vi.mock('sonner', () => ({
    toast: { info: vi.fn(), success: vi.fn(), error: vi.fn() },
}));

const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        {children}
    </QueryClientProvider>
);

describe('BlueprintWizard', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockAuthFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve([]) });
    });

    it('renders wizard title when open', () => {
        render(<BlueprintWizard open={true} onOpenChange={vi.fn()} />, { wrapper: Wrapper });
        expect(screen.getByText(/Foundry Wizard/i)).toBeInTheDocument();
    });

    it('does not render content when closed', () => {
        render(<BlueprintWizard open={false} onOpenChange={vi.fn()} />, { wrapper: Wrapper });
        expect(screen.queryByText(/Foundry Wizard/i)).not.toBeInTheDocument();
    });
});
```

### WIZ-02: Auto-Dependency Injection Assertion
```typescript
import { toast } from 'sonner';

it('auto-injects runtime_dependencies when tool is selected', async () => {
    mockAuthFetch.mockImplementation((url: string) => {
        if (url === '/api/blueprints') return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
        if (url === '/api/approved-os') return Promise.resolve({ ok: true, json: () => Promise.resolve([
            { id: 1, image_uri: 'debian:12', friendly_name: 'Debian 12', os_family: 'DEBIAN', is_compliant: true, created_at: '2025-01-01' }
        ]) });
        if (url === '/api/smelter/ingredients') return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
        if (url === '/api/capability-matrix') return Promise.resolve({ ok: true, json: () => Promise.resolve([
            { id: 1, tool_id: 'python-runner', base_os_family: 'DEBIAN', is_active: true, runtime_dependencies: ['requests', 'httpx'], injection_recipe: '', validation_cmd: '' }
        ]) });
        return Promise.resolve({ ok: false, json: () => Promise.resolve({}) });
    });

    // Navigate to Step 4, click tool, assert toast.info and package state
    // ... (navigate through steps 1-4 first)
    const toolCard = await screen.findByText('python-runner');
    fireEvent.click(toolCard);

    expect(toast.info).toHaveBeenCalledWith(
        expect.stringContaining('2 dependencies'),
        expect.objectContaining({ description: 'requests, httpx' })
    );
});
```

### WIZ-03: Vulnerable Ingredient Badge
```typescript
it('shows vulnerable badge for is_vulnerable ingredients', async () => {
    mockAuthFetch.mockImplementation((url: string) => {
        if (url === '/api/smelter/ingredients') return Promise.resolve({ ok: true, json: () => Promise.resolve([
            { id: 1, name: 'evil-pkg', version_constraint: '==1.0', os_family: 'DEBIAN', is_vulnerable: true, mirror_status: 'MIRRORED' }
        ]) });
        // ... other mocks
    });

    // Navigate to Step 3
    // ...

    expect(await screen.findByText('Vulnerable')).toBeInTheDocument();
});
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw JSON textarea for blueprint creation | 5-step guided wizard with guardrails | Phase 14 | Users cannot accidentally produce invalid blueprints |
| No dependency resolution in UI | Auto-injection of `runtime_dependencies` on tool select | Phase 14 (Plan 04) | Reduces hand-crafting of package lists |
| Blueprint creation had no clone path | Clone from existing blueprint in Step 1 | Phase 14 (Plan 01) | Accelerates iteration from proven blueprints |

**Deprecated/outdated:**
- The old `CreateBlueprintDialog` that accepted raw JSON directly is superseded by `BlueprintWizard`. The `Templates.tsx` view was updated in Plan 01 to use the wizard. The legacy dialog code should not be restored.

---

## Open Questions

1. **Draft persistence via backend DRAFT status**
   - What we know: CONTEXT.md references `status: DRAFT` field as available from Phase 17/19. The wizard uses local React state only — closing the dialog discards state.
   - What's unclear: Phase 17/19 status fields apply to `ScheduledJob`, not `Blueprint`. Blueprint drafts may require a different approach (localStorage or a new Blueprint status).
   - Recommendation: For the test plan, treat draft persistence as a future enhancement. Validate that the current wizard correctly resets state on open (`useEffect` on `open` prop).

2. **Side-by-side diff for clone/edit flows**
   - What we know: CONTEXT.md locked "real-time diffing" as a requirement. The current Step 5 shows a JSON preview but not a diff against the source blueprint.
   - What's unclear: Whether the planner considers the JSON preview sufficient for WIZ-01/02/03 or whether a diff panel is a separate gap.
   - Recommendation: Treat diff as a stretch goal outside the three WIZ requirements. Flag in the plan as a known gap if visible side-by-side comparison is not yet rendered.

---

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json`. This section is required.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | vitest (already configured) |
| Config file | `puppeteer/dashboard/vitest.config.ts` |
| Quick run command | `cd puppeteer/dashboard && npx vitest run src/components/__tests__/BlueprintWizard.test.tsx` |
| Full suite command | `cd puppeteer/dashboard && npm run test` |

### Phase Requirements — Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WIZ-01 | Wizard renders all 5 steps and submits a valid blueprint payload without JSON input | unit (RTL) | `npx vitest run src/components/__tests__/BlueprintWizard.test.tsx` | ❌ Wave 0 |
| WIZ-01 | `blueprintToJson` helper produces correct schema from Composition state | unit (pure) | `npx vitest run src/components/__tests__/BlueprintWizard.test.tsx` | ❌ Wave 0 |
| WIZ-02 | Selecting a tool with `runtime_dependencies` adds packages to state and fires toast | unit (RTL) | `npx vitest run src/components/__tests__/BlueprintWizard.test.tsx` | ❌ Wave 0 |
| WIZ-02 | De-selecting a tool does NOT remove its auto-injected packages (permissive model) | unit (RTL) | `npx vitest run src/components/__tests__/BlueprintWizard.test.tsx` | ❌ Wave 0 |
| WIZ-03 | `is_vulnerable: true` ingredient renders "Vulnerable" badge in Step 3 | unit (RTL) | `npx vitest run src/components/__tests__/BlueprintWizard.test.tsx` | ❌ Wave 0 |
| WIZ-03 | `mirror_status !== 'MIRRORED'` ingredient renders "Sync Pending" amber badge | unit (RTL) | `npx vitest run src/components/__tests__/BlueprintWizard.test.tsx` | ❌ Wave 0 |
| All | Wizard resets state on re-open (open prop toggles) | unit (RTL) | `npx vitest run src/components/__tests__/BlueprintWizard.test.tsx` | ❌ Wave 0 |
| All | "Advanced (JSON)" toggle converts wizard state to readable JSON text | unit (RTL) | `npx vitest run src/components/__tests__/BlueprintWizard.test.tsx` | ❌ Wave 0 |
| All | OS-family filter in Step 4 only shows tools with matching `base_os_family` | unit (RTL) | `npx vitest run src/components/__tests__/BlueprintWizard.test.tsx` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd puppeteer/dashboard && npx vitest run src/components/__tests__/BlueprintWizard.test.tsx`
- **Per wave merge:** `cd puppeteer/dashboard && npm run test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `puppeteer/dashboard/src/components/__tests__/BlueprintWizard.test.tsx` — covers WIZ-01, WIZ-02, WIZ-03 (does not exist; must be created before any implementation plan runs)
- [ ] No framework install needed — vitest, @testing-library/react, @testing-library/jest-dom are all present in node_modules and configured

*(Note: `puppeteer/dashboard/src/test/setup.ts` already exists and is referenced by vitest.config.ts — no new setup file needed.)*

---

## Sources

### Primary (HIGH confidence)
- Direct file inspection of `BlueprintWizard.tsx` — implementation confirmed as complete across all 5 plans
- `vitest.config.ts` — test framework, jsdom environment, path aliases confirmed
- `14-CONTEXT.md` — locked decisions confirmed
- `14-01-SUMMARY.md` through `14-05-SUMMARY.md` — implementation status confirmed

### Secondary (MEDIUM confidence)
- `src/components/__tests__/AddNodeModal.test.tsx` — established vitest + RTL + vi.mock pattern
- `src/views/__tests__/JobDefinitions.test.tsx` — established TanStack Query mock pattern with `mockAuthFetch`
- `.planning/config.json` — `nyquist_validation: true` confirmed

### Tertiary (LOW confidence)
- None — all findings verified from project source files

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified from vitest.config.ts and existing test files
- Architecture: HIGH — patterns extracted directly from existing tests in this codebase
- Pitfalls: HIGH — derived from reading BlueprintWizard.tsx implementation and Radix Dialog behavior
- Validation architecture: HIGH — test commands verified against installed tooling

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable UI pattern domain — no fast-moving dependencies)
