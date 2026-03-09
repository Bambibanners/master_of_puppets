---
phase: 10
slug: windows-installer-fix
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Pester 5.x (PowerShell) |
| **Config file** | None — Wave 0 creates `puppeteer/installer/tests/installer.Tests.ps1` |
| **Quick run command** | `Invoke-Pester puppeteer/installer/tests/installer.Tests.ps1 -Output Minimal` |
| **Full suite command** | `Invoke-Pester puppeteer/installer/tests/ -Output Detailed` |
| **Estimated runtime** | ~10 seconds |

Note: Pester must be installed. Install with `Install-Module -Name Pester -Force -SkipPublisherCheck` in PowerShell (available on Linux via `pwsh`).

---

## Sampling Rate

- **After every task commit:** Run `Invoke-Pester puppeteer/installer/tests/installer.Tests.ps1 -Output Minimal`
- **After every plan wave:** Run `Invoke-Pester puppeteer/installer/tests/ -Output Detailed`
- **Before `/gsd:verify-work`:** Full suite must be green + manual WIN-06 smoke + manual WIN-07 check
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 0 | WIN-01..05 | unit | `Invoke-Pester puppeteer/installer/tests/installer.Tests.ps1 -Output Minimal` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 0 | WIN-06 | smoke | Manual (podman build) | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 1 | WIN-01 | unit (Pester Mock) | `Invoke-Pester puppeteer/installer/tests/installer.Tests.ps1 -Output Minimal` | ✅ W0 | ⬜ pending |
| 10-02-02 | 02 | 1 | WIN-02 | unit (Pester Mock) | `Invoke-Pester puppeteer/installer/tests/installer.Tests.ps1 -Output Minimal` | ✅ W0 | ⬜ pending |
| 10-02-03 | 02 | 1 | WIN-03 | unit (Pester Mock) | `Invoke-Pester puppeteer/installer/tests/installer.Tests.ps1 -Output Minimal` | ✅ W0 | ⬜ pending |
| 10-02-04 | 02 | 1 | WIN-04 | code review | Manual | N/A | ⬜ pending |
| 10-02-05 | 02 | 1 | WIN-05 | unit (Pester Mock) | `Invoke-Pester puppeteer/installer/tests/installer.Tests.ps1 -Output Minimal` | ✅ W0 | ⬜ pending |
| 10-03-01 | 03 | 2 | WIN-06 | smoke | Manual (podman build on Linux/WSL2) | ✅ W0 | ⬜ pending |
| 10-03-02 | 03 | 2 | WIN-07 | manual | Human verification | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `puppeteer/installer/tests/installer.Tests.ps1` — Pester test stubs for WIN-01 through WIN-05
- [ ] `puppeteer/installer/loader/Containerfile` — Loader container image definition (WIN-06)
- [ ] Pester framework available (`pwsh` + `Install-Module Pester`)

*Wave 0 creates the test file and loader Containerfile before fix work begins.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `podman run` uses splatting not Invoke-Expression | WIN-04 | Code review — static analysis only | Review diff for `@podmanArgs` splat pattern vs string assembly |
| Loader container builds successfully | WIN-06 | Requires podman to be installed | `cd puppeteer/installer/loader && podman build -t mop-loader .` |
| Method 1 end-to-end on Windows/WSL2 | WIN-07 | Requires Windows hardware or WSL2 | Run Method 1 on Windows, verify node enrolls and heartbeats |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
