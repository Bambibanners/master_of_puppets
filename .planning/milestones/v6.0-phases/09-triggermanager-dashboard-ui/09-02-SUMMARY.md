---
phase: 09-triggermanager-dashboard-ui
plan: "02"
subsystem: frontend
tags: [react, admin, triggers, ui, dialog, alertdialog]
dependency_graph:
  requires: ["09-01"]
  provides: ["complete-triggermanager-ui"]
  affects: ["puppeteer/dashboard/src/views/Admin.tsx"]
tech_stack:
  added: []
  patterns:
    - "AlertDialog for destructive confirmations (disable trigger)"
    - "Dialog for one-time secret reveal (token rotation)"
    - "useMutation for PATCH toggle and POST regenerate-token"
    - "Empty state with CTA when data array is length 0"
key_files:
  created: []
  modified:
    - puppeteer/dashboard/src/views/Admin.tsx
decisions:
  - "Copy Token uses navigator.clipboard directly (no confirmation dialog) — immediate UX, matches plan locked decision"
  - "Enable sends PATCH immediately with no dialog — only Disable requires confirmation per locked decision"
  - "Token reveal dialog cannot be bypassed — user must click 'I have saved the token' to close"
metrics:
  duration: "2 minutes"
  completed: "2026-03-08T20:55:00Z"
  tasks_completed: 2
  files_modified: 1
---

# Phase 09 Plan 02: TriggerManager UI Fixes and Feature Completion Summary

Admin.tsx TriggerManager compile errors fixed and three UI features added: Active/Inactive toggle with confirmation, Copy Token + Rotate Key with one-time reveal modal, and empty state.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Fix compile errors — add all missing imports | c5e4c3e | Admin.tsx |
| 2 | Extend TriggerManager with toggle, Copy Token, Rotate Key, empty state | ba46dcb | Admin.tsx |

## Build Output Confirmation

Task 1 build:
- Exit code: 0
- Admin chunk: 20.24 kB (gzip: 5.54 kB)
- No TypeScript errors referencing Dialog, Label, or AlertDialog

Task 2 build:
- Exit code: 0
- Admin chunk: 25.04 kB (gzip: 6.47 kB) — grew by ~4.8 kB as expected from added feature code
- No TypeScript errors

## New State Variables Added

Six new state variables added to TriggerManager (after `const [newTrigger, ...]`):

1. `isDisableConfirmOpen: boolean` — controls the disable confirmation AlertDialog
2. `pendingToggleTrigger: any` — holds the trigger being toggled (set before opening disable dialog)
3. `isRotateConfirmOpen: boolean` — controls the rotate token confirmation AlertDialog
4. `isTokenRevealOpen: boolean` — controls the one-time token reveal Dialog
5. `newToken: string | null` — holds the newly generated secret_token from rotateMutation response
6. `pendingRotateTrigger: any` — holds the trigger being rotated (set before opening rotate dialog)

## New Mutations Added

Two new mutations added after `deleteMutation`:

**toggleMutation:**
- `mutationFn`: PATCH `/api/admin/triggers/${id}` with body `{ is_active: boolean }`
- `onSuccess`: invalidates `['automation-triggers']`, shows toast, closes disable dialog

**rotateMutation:**
- `mutationFn`: POST `/api/admin/triggers/${id}/regenerate-token` (no body)
- `onSuccess`: invalidates `['automation-triggers']`, sets `newToken` from `data.secret_token`, closes rotate dialog, opens token reveal dialog, shows toast

## Column Count Verification

Table header now has 5 `<TableHead>` elements: Name, Slug, Target Job, Status, Actions.

Empty state uses `colSpan={5}` — matches the 5-column count exactly.

## Imports Added

To lucide-react:
- `AlertTriangle` (added to existing import block)

New import blocks added before `import { authenticatedFetch } from '../auth'`:
- `Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter` from `@/components/ui/dialog`
- `AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel, AlertDialogAction` from `@/components/ui/alert-dialog`
- `Label` from `@/components/ui/label`

## Deviations from Plan

None - plan executed exactly as written. All patterns matched the ServicePrincipals.tsx one-time reveal reference described in the plan interfaces section.

## Self-Check: PASSED

- [x] `puppeteer/dashboard/src/views/Admin.tsx` exists and contains all new code
- [x] Commit c5e4c3e exists (Task 1: import fixes)
- [x] Commit ba46dcb exists (Task 2: feature additions)
- [x] Build exit code 0 verified after both tasks
- [x] colSpan=5 matches 5-column table header
- [x] All 3 dialogs present: disable confirm (AlertDialog), rotate confirm (AlertDialog), token reveal (Dialog)
