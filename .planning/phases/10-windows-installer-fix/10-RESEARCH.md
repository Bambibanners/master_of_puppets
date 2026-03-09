# Phase 10: Windows Installer Fix - Research

**Researched:** 2026-03-09
**Domain:** PowerShell installer scripting, Podman on Windows (named pipe / WSL2 socket), container socket passthrough
**Confidence:** MEDIUM — core Podman-on-Windows socket model verified via official sources; installer code fully read; Windows runtime testing requires a real Windows machine

---

## Summary

Phase 10 fixes a single, specific broken code path in `puppeteer/installer/install_universal.ps1`: the **Loader deployment method (Method 1)** for the `Agent` role. When a user picks `[1] Automatic (Loader Container)`, the script attempts to run a container and mount the Podman socket as `-v /var/run/podman.sock:/run/podman/podman.sock`. On Windows this path does not exist. Podman on Windows exposes its API via a **named pipe** (`\\.\pipe\podman-machine-default`) rather than a Unix socket file, and named pipes cannot be mounted into containers with `-v`. The script's existing comment acknowledges this is unresolved: "Simple volume mount won't work for Pipe -> File."

The correct fix for Windows is to detect the socket path using `podman machine inspect`, then choose between:
1. **WSL-bridge unix socket** (`/mnt/wsl/podman-sockets/<machine>/podman-root.sock`) — mountable as a normal `-v` bind, accessible when running from inside a WSL distribution
2. **TCP relay** — `podman system service --time=0 tcp:127.0.0.1:2375` starts a temporary HTTP listener; the container receives `DOCKER_HOST=tcp://host.docker.internal:2375`
3. **DOCKER_HOST environment variable only** — pass `DOCKER_HOST=npipe:////./pipe/podman-machine-default` via `-e`; works if the loader container image includes a Podman/Docker client that understands the Windows named pipe protocol (practically impossible inside a Linux container)

Option 1 (WSL socket bind mount) is the most reliable when the user is running PowerShell from inside a WSL distribution. Option 2 (TCP relay) works from native Windows PowerShell. The script must detect whether `$IsWindows` is true (native PowerShell) or false (WSL-hosted PowerShell) and branch accordingly.

Beyond the named-pipe bug, there are several secondary issues to address in the same edit: the `Invoke-Expression $RunCmd` anti-pattern for command construction, the hardcoded `podman-compose` dependency for the loader path (where compose is unnecessary — the loader container handles it), and the absence of any validation that a Podman machine is actually running before the `podman run` call.

**Primary recommendation:** On Windows, resolve the Podman socket path dynamically using `podman machine inspect --format '{{.ConnectionInfo.PodmanPipe.Path}}'`, then relay via TCP (`podman system service`) rather than a named-pipe volume mount. Pass `DOCKER_HOST=tcp://host.docker.internal:2375` into the loader container. Add a `podman machine list` guard before the run.

---

## Current State Analysis

### What Method 1 (Loader) Does

```
if ($Method -eq "1") {
    podman build -t puppeteer-loader -f loader/Containerfile .
    $SocketMount = "-v /var/run/podman.sock:/run/podman/podman.sock"
    # $IsWindows branch is a no-op (only logs a warning, does not fix mount)
    $RunCmd = "podman run --privileged --rm -it $SocketMount -v ${PWD}:/app puppeteer-loader"
    Invoke-Expression $RunCmd
}
```

**Broken points:**
1. `/var/run/podman.sock` does not exist on Windows hosts — `podman machine` runs in a WSL2 VM, not on the host filesystem
2. `$IsWindows` branch logs a warning but still uses the broken Linux socket path
3. `Invoke-Expression` on a string-assembled command is fragile (path with spaces fails)
4. `loader/Containerfile` is referenced but not present in the installer directory — this is a missing asset
5. No guard to check that `podman machine` is started before attempting `podman run`
6. The `podman-compose` check at the top of the script is irrelevant for the Loader path (the loader handles compose, not the host)

### Node Role Path (Already Works on Windows — No Fix Needed)

The Node role path (`$Role -eq "Node"`) uses `curl.exe` to download `node-compose.yaml`, then calls `podman-compose -f node-compose.yaml up -d --scale node=$Count`. This works correctly on Windows and does not require socket access. The node containers themselves use `EXECUTION_MODE=direct` (as documented in cross-network validation) since DinD inside Windows Podman machine containers has cgroup v2 constraints — `direct` mode in `runtime.py` bypasses socket access entirely.

---

## Standard Stack

### Core (Windows PowerShell Scripting)

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| PowerShell | 5.1+ or 7.x | Script runtime | Already the installer's language |
| `podman machine inspect` | Podman 4.x+ | Query named pipe / socket path | Official API for dynamic discovery |
| `podman system service` | Podman 4.x+ | Expose Podman API over TCP | Required for container-side access on Windows |
| Pester | 5.x | PowerShell unit testing | Standard PS test framework; `Install-Module Pester` |

### Podman Windows Socket Model (HIGH confidence)

| Scenario | Socket Mechanism | Path |
|----------|-----------------|------|
| Native Windows PowerShell | Named pipe | `\\.\pipe\podman-machine-default` |
| DOCKER_HOST (PS syntax) | npipe scheme | `npipe:////./pipe/podman-machine-default` |
| WSL distribution (Linux) | Unix socket via `/mnt/wsl` | `/mnt/wsl/podman-sockets/<machine>/podman-root.sock` |
| TCP relay (any) | HTTP socket service | `tcp://127.0.0.1:2375` started by `podman system service` |

**Getting the pipe path dynamically:**
```powershell
# Source: Podman Desktop docs + containers/podman issue #19918
$PipePath = podman machine inspect --format '{{.ConnectionInfo.PodmanPipe.Path}}'
# Returns: \\.\pipe\podman-machine-default  (on Windows)
# PodmanSocket.Path is NULL on Windows — use PodmanPipe.Path instead
```

**Getting the WSL unix socket path (if running from WSL):**
```bash
# Source: Podman Desktop docs — accessing Podman from another WSL instance
/mnt/wsl/podman-sockets/podman-machine-default/podman-root.sock
```

**Starting TCP relay (native Windows):**
```powershell
# Source: containers/podman discussions #20531
$job = Start-Job { podman system service --time=0 tcp:127.0.0.1:2375 }
Start-Sleep -Seconds 2
# Now pass -e DOCKER_HOST=tcp://host.docker.internal:2375 into container
```

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `wsl.exe -l -v` | OS built-in | Detect if WSL is running | Determine WSL socket availability |
| `podman machine list` | Podman 4.x+ | Verify machine is started | Guard before socket-dependent operations |

---

## Architecture Patterns

### Recommended Fix: Two-Branch Socket Resolution

```
Windows Podman socket strategy:
  ├── Running from WSL distro? (check $env:WSL_DISTRO_NAME or wsl.exe)
  │    └── Use: -v /mnt/wsl/podman-sockets/<machine>/podman-root.sock:/run/podman/podman.sock
  └── Running from native Windows PowerShell
       └── Start: podman system service --time=0 tcp:127.0.0.1:2375
           Pass: -e DOCKER_HOST=tcp://host.docker.internal:2375
           (add --add-host=host.docker.internal:host-gateway or use host.docker.internal)
```

### Pattern 1: Dynamic Socket Discovery (Windows)

**What:** Query `podman machine inspect` to get the current pipe path rather than hardcoding
**When to use:** At the start of the Method 1 (Loader) path, before any `podman run`
**Key insight:** `PodmanSocket.Path` is always null on Windows; must use `PodmanPipe.Path`

```powershell
# Source: https://github.com/containers/podman/issues/19918 + Podman Desktop docs
function Get-PodmanSocketInfo {
    # Check if machine is running
    $machines = podman machine list --format "{{.Name}} {{.Running}}" 2>$null
    if (-not ($machines -match "true")) {
        Write-Error "No running Podman machine found. Run: podman machine start"
    }
    # Get pipe path
    $pipePath = podman machine inspect --format '{{.ConnectionInfo.PodmanPipe.Path}}' 2>$null
    return $pipePath
}
```

### Pattern 2: TCP Relay for Loader Container

**What:** Start a temporary `podman system service` TCP listener; pass host address to container
**When to use:** Native Windows PowerShell (not WSL), Method 1 Loader path only

```powershell
# Start relay in background PowerShell job
$relayJob = Start-Job -ScriptBlock {
    podman system service --time=0 tcp:127.0.0.1:2375
}
# Wait for it to be ready
Start-Sleep -Seconds 3
# Run loader with DOCKER_HOST
podman run --rm -it `
    --add-host=host.docker.internal:host-gateway `
    -e DOCKER_HOST=tcp://host.docker.internal:2375 `
    -v "${PWD}:/app" `
    puppeteer-loader
# Cleanup relay
Stop-Job $relayJob; Remove-Job $relayJob
```

### Pattern 3: Replace Invoke-Expression with Splatting

**What:** Build args as array, pass with `@` splatting — avoids shell splitting issues
**When to use:** All `podman run` calls in the script

```powershell
# BEFORE (broken for paths with spaces):
$RunCmd = "podman run --privileged --rm -it $SocketMount -v ${PWD}:/app puppeteer-loader"
Invoke-Expression $RunCmd

# AFTER (correct PowerShell idiom):
$RunArgs = @("run", "--rm", "-it", "--add-host=host.docker.internal:host-gateway",
             "-e", "DOCKER_HOST=tcp://host.docker.internal:2375",
             "-v", "${PWD}:/app", "puppeteer-loader")
& podman @RunArgs
```

### Anti-Patterns to Avoid

- **`-v /var/run/podman.sock:...` on Windows:** The host socket path does not exist; this silently passes a missing mount to Podman, which may create an empty directory instead of failing clearly.
- **`Invoke-Expression` on string commands:** Path spaces cause argument splitting; use splatting (`& cmd @args`) instead.
- **`--privileged` without reason:** The loader container likely does not need `--privileged` if using TCP relay rather than socket binding. Remove if not required by the loader's actual operations.
- **Assuming `podman machine` is running:** `podman run` against a stopped machine returns a confusing error. Always check `podman machine list` first.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Detect Podman pipe path | Custom registry parsing | `podman machine inspect --format '{{.ConnectionInfo.PodmanPipe.Path}}'` | Official API, handles multi-machine setups |
| Check if Podman machine is running | Parsing process list | `podman machine list --format json` + `ConvertFrom-Json` | Structured, reliable |
| PowerShell unit tests | Custom test runner | Pester 5.x | Standard; supports Mock for external commands |
| TCP socket service | Custom TCP proxy | `podman system service --time=0 tcp:127.0.0.1:2375` | Built into Podman 4.x+ |

---

## Common Pitfalls

### Pitfall 1: `PodmanSocket.Path` is Null on Windows

**What goes wrong:** `podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}'` returns an empty string on Windows even when the machine is running.
**Why it happens:** On Windows, Podman uses a named pipe (`PodmanPipe`), not a Unix socket file. The `PodmanSocket` field is a Linux/macOS concept.
**How to avoid:** Always use `PodmanPipe.Path` on Windows. If you need a portable command, probe for both.
**Warning signs:** Empty path returned from inspect; no socket file at the expected location.

### Pitfall 2: Named Pipe Cannot Be Bind-Mounted Into Linux Container

**What goes wrong:** `-v \\.\pipe\podman-machine-default:/run/podman/podman.sock` fails silently or creates a directory.
**Why it happens:** Windows named pipes are a Windows kernel object, not a filesystem path. The Linux container inside the Podman WSL2 VM has no mechanism to access them via volume bind.
**How to avoid:** Use TCP relay (`podman system service`) for the loader container to communicate back to the host Podman. Or, if invoking from WSL, use the WSL-shared unix socket at `/mnt/wsl/podman-sockets/`.
**Warning signs:** Loader container starts but cannot run `podman` or `podman-compose` commands; socket-related errors inside the container.

### Pitfall 3: `host.docker.internal` Resolution Inside Podman on Windows

**What goes wrong:** The container cannot resolve `host.docker.internal` to reach the TCP relay.
**Why it happens:** Unlike Docker Desktop, Podman on Windows does not automatically inject the `host.docker.internal` host entry into containers.
**How to avoid:** Pass `--add-host=host.docker.internal:host-gateway` to `podman run`. Verify with `podman run --rm alpine nslookup host.docker.internal`.
**Warning signs:** Connection refused / no route to host when container tries to reach `tcp://host.docker.internal:2375`.

### Pitfall 4: `podman machine` Not Started

**What goes wrong:** `podman run` returns `Error: failed to connect: connection refused` rather than the expected execution error.
**Why it happens:** The Podman CLI on Windows is a remote client; it requires the WSL2-based `podman machine` VM to be running.
**How to avoid:** Check `podman machine list` at the top of the script and fail with a clear message if no machine is in `Running` state.
**Warning signs:** Any `podman` command fails with a connection error even though `podman` binary is on PATH.

### Pitfall 5: `loader/Containerfile` Missing Asset

**What goes wrong:** `podman build -t puppeteer-loader -f loader/Containerfile .` fails immediately because `loader/Containerfile` does not exist in the repo.
**Why it happens:** The Loader path was designed with a deferred asset — the Containerfile was never created.
**How to avoid:** The Phase 10 plan must either create `puppeteer/installer/loader/Containerfile` or change Method 1 to pull a pre-built image. Creating the Containerfile is cleaner and self-contained.
**Warning signs:** `ERRO[0000] error building image` on the build step.

### Pitfall 6: `podman-compose` Check Blocks Loader Path

**What goes wrong:** The script validates `podman-compose` is on PATH before the user even selects a method. Users without `podman-compose` cannot use Method 1 even though Method 1 doesn't use it.
**Why it happens:** Platform validation runs unconditionally before the method selection dialog.
**How to avoid:** Move `podman-compose` validation inside the `else` branch (Method 2 only). Method 1 (Loader) needs only `podman` itself.

---

## Code Examples

### Detect and Guard Podman Machine State

```powershell
# Source: containers/podman issue #19918 + Podman Desktop docs
function Assert-PodmanMachineRunning {
    $machineJson = podman machine list --format json 2>$null | ConvertFrom-Json
    $running = $machineJson | Where-Object { $_.Running -eq $true }
    if (-not $running) {
        Write-Error "No Podman machine is running. Start one with: podman machine start"
    }
    return $running[0].Name
}
```

### Build Loader Run Args (Correct Splatting Pattern)

```powershell
# Source: PowerShell docs — splatting with external commands
$LoaderArgs = @(
    "run", "--rm", "-it",
    "--add-host=host.docker.internal:host-gateway",
    "-e", "DOCKER_HOST=tcp://host.docker.internal:2375",
    "-v", "${PWD}:/app",
    "-w", "/app",
    "puppeteer-loader"
)
& podman @LoaderArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Loader container failed with exit code $LASTEXITCODE"
}
```

### Minimal loader/Containerfile

```dockerfile
# Needs: podman or docker CLI + podman-compose inside the container
# Base: Fedora (ships podman), or Ubuntu + install podman-compose
FROM fedora:40
RUN dnf install -y podman podman-compose python3 && dnf clean all
WORKDIR /app
CMD ["podman-compose", "-f", "compose.server.yaml", "up", "-d"]
```

### Pester Test Skeleton (for socket detection logic)

```powershell
# Source: pester.dev/docs/quick-start
# File: puppeteer/installer/tests/installer.Tests.ps1
Describe "Get-PodmanSocketInfo" {
    Context "When podman machine is running" {
        BeforeEach {
            Mock podman { return '\\.\pipe\podman-machine-default' } `
                -ParameterFilter { $args[0] -eq 'machine' -and $args[1] -eq 'inspect' }
        }
        It "returns a non-empty pipe path" {
            $path = Get-PodmanSocketInfo
            $path | Should -Not -BeNullOrEmpty
        }
    }
    Context "When no machine is running" {
        BeforeEach {
            Mock podman { return '' } `
                -ParameterFilter { $args[0] -eq 'machine' -and $args[1] -eq 'list' }
        }
        It "throws an error" {
            { Assert-PodmanMachineRunning } | Should -Throw
        }
    }
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded `/var/run/podman.sock` | Dynamic `podman machine inspect` query | Podman 4.0+ (2022) | Socket path varies by machine name and user |
| Named pipe volume mount | TCP relay via `podman system service` | Podman 3.4+ (2021) | Only viable cross-container approach on Windows |
| `Invoke-Expression` string commands | Splatting with `& cmd @args` | PowerShell 3+ | Handles spaces, special chars, avoids injection |
| Unconditional platform checks | Method-gated dependency checks | Best practice | Avoids blocking Method 1 users who lack compose |

**Deprecated/outdated:**
- `-v /var/run/podman.sock`: Works only on Linux; not applicable to Windows Podman machine
- `--privileged` for socket access: Not required when using TCP relay; represents unnecessary privilege escalation

---

## Open Questions

1. **Does the loader/Containerfile need to exist or will Method 1 pull a remote image?**
   - What we know: The current script does `podman build -t puppeteer-loader -f loader/Containerfile .`, expecting a local file
   - What's unclear: Whether the project wants to maintain this Containerfile or pivot to a `podman pull` of a published image
   - Recommendation: Create a minimal `loader/Containerfile` in `puppeteer/installer/` as part of this phase; keeps everything self-contained and offline-capable

2. **Should Method 1 (Loader) be Windows-only or work on Linux too?**
   - What we know: Method 1 is currently only presented in the `-Role Agent` path; Linux server deployments use `install_universal.sh`
   - What's unclear: Whether there is a Linux user base for the PS1 Agent role path
   - Recommendation: Keep Linux socket path (`/var/run/podman.sock`) for the non-Windows branch; no change needed there

3. **Can we test the Loader path without a real Windows machine?**
   - What we know: No Windows hardware in the project; WSL2 is available on the dev host
   - What's unclear: Whether WSL2 `pwsh` + Podman machine faithfully replicates native Windows PowerShell behavior
   - Recommendation: Write Pester unit tests that Mock the `podman` command for the logic paths; mark the actual end-to-end loader launch as a **manual verification step** in the verification plan. The Pester tests cover the critical detection/branching logic without requiring Windows hardware.

4. **Should `podman-compose` validation be entirely removed from the Podman platform check block?**
   - What we know: Method 1 does not use `podman-compose`; only Method 2 does
   - What's unclear: Whether existing deployments rely on the early validation as a user-facing dependency check
   - Recommendation: Move `podman-compose` check inside the `else` (Method 2) branch; document in comments

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Pester 5.x (PowerShell) |
| Config file | None — Wave 0 creates `puppeteer/installer/tests/installer.Tests.ps1` |
| Quick run command | `Invoke-Pester puppeteer/installer/tests/installer.Tests.ps1 -Output Minimal` |
| Full suite command | `Invoke-Pester puppeteer/installer/tests/ -Output Detailed` |

Note: Pester must be installed on the test machine. Install with `Install-Module -Name Pester -Force -SkipPublisherCheck` in PowerShell (available on Linux via `pwsh`).

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WIN-01 | Machine-running guard exits with clear error when no machine running | unit (Pester Mock) | `Invoke-Pester ... -Output Minimal` | Wave 0 |
| WIN-02 | Socket resolver returns non-empty pipe path when machine is up | unit (Pester Mock) | `Invoke-Pester ... -Output Minimal` | Wave 0 |
| WIN-03 | TCP relay is started before loader container | unit (Pester Mock) | `Invoke-Pester ... -Output Minimal` | Wave 0 |
| WIN-04 | `podman run` args use splatting, not Invoke-Expression | code review / static | Manual | N/A |
| WIN-05 | `podman-compose` check only runs for Method 2 | unit (Pester Mock) | `Invoke-Pester ... -Output Minimal` | Wave 0 |
| WIN-06 | `loader/Containerfile` exists and builds successfully | smoke (podman build) | Manual on Linux/WSL2 | Wave 0 |
| WIN-07 | Method 1 end-to-end on actual Windows or WSL2 | manual | Human verification | N/A — manual only |

### Sampling Rate
- **Per task commit:** `Invoke-Pester puppeteer/installer/tests/installer.Tests.ps1 -Output Minimal`
- **Per wave merge:** `Invoke-Pester puppeteer/installer/tests/ -Output Detailed`
- **Phase gate:** All Pester tests green + manual WIN-06 smoke + manual WIN-07 check before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `puppeteer/installer/tests/installer.Tests.ps1` — Pester tests for WIN-01 through WIN-05
- [ ] `puppeteer/installer/loader/Containerfile` — Loader container image definition (WIN-06)
- [ ] Pester framework: `Install-Module -Name Pester -Force -SkipPublisherCheck` (if not present in pwsh)

---

## Sources

### Primary (HIGH confidence)
- [containers/podman issue #19918](https://github.com/containers/podman/issues/19918) — `PodmanSocket.Path` is null on Windows; must use `PodmanPipe.Path`
- [Podman Desktop docs — DOCKER_HOST variable](https://podman-desktop.io/docs/migrating-from-docker/using-the-docker_host-environment-variable) — Windows named pipe format `npipe:////./pipe/podman-machine-default`
- [Podman Desktop docs — Accessing from another WSL instance](https://podman-desktop.io/docs/podman/accessing-podman-from-another-wsl-instance) — `/mnt/wsl/podman-sockets/<machine>/podman-root.sock` path
- [pester.dev](https://pester.dev/docs/quick-start) — Pester 5.x quick start, Mock syntax

### Secondary (MEDIUM confidence)
- [containers/podman discussions #20531](https://github.com/containers/podman/discussions/20531) — `podman system service --time=0 tcp:127.0.0.1:2375` TCP relay pattern
- [containers/podman issue #19362](https://github.com/containers/podman/issues/19362) — Feature request to mount named pipe into container confirms it is NOT natively supported
- [Podman for Windows tutorial](https://github.com/containers/podman/blob/main/docs/tutorials/podman-for-windows.md) — Authoritative Windows socket documentation

### Tertiary (LOW confidence)
- WebSearch results about `host.docker.internal` injection for Podman on Windows — needs validation in practice; pattern well-established in Docker Desktop but less documented for Podman

---

## Metadata

**Confidence breakdown:**
- Podman Windows socket model: HIGH — verified via official Podman issue tracker + Podman Desktop docs
- Loader path bug identification: HIGH — read directly from `install_universal.ps1`; bugs self-evident from the code comments
- TCP relay approach: MEDIUM — documented in Podman discussions; not verified end-to-end without Windows hardware
- `host.docker.internal` resolution in Podman: LOW — pattern well-known in Docker Desktop; Podman on Windows behavior less documented
- Pester testing approach: HIGH — official PowerShell testing standard; syntax verified via pester.dev

**Research date:** 2026-03-09
**Valid until:** 2026-09-09 (Podman Windows architecture stable; named pipe behavior unlikely to change)
