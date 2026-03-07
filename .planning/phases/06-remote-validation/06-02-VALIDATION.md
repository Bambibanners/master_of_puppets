---
phase: 06-02
slug: linux-universal-installer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 06-02 — Validation Strategy: Linux Universal Installer

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend unit) + Python integration test harness (installer) |
| **Config file** | `puppeteer/pytest.ini` (if exists) or default |
| **Quick run command** | `cd puppeteer && pytest tests/ -x -q` |
| **Full suite command** | `cd puppeteer && pytest tests/` |
| **Integration harness** | `python3 /home/thomas/Development/mop_validation/scripts/test_installer_lxc.py` |
| **Estimated runtime** | ~5 min (integration, including LXC spin-up/teardown) |

Note: The installer itself is a bash script — validation is primarily integration-level, not unit-level. The Python test harness in `mop_validation/scripts/` is the appropriate home for integration tests.

---

## Sampling Rate

- **After every task commit:** `cd puppeteer && pytest tests/ -x -q`
- **After every plan wave:** `cd puppeteer && pytest tests/` + manual verify harness output
- **Before `/gsd:verify-work`:** Full backend suite green + manual heartbeat visible in dashboard
- **Max feedback latency:** ~5 minutes (integration), <30s (unit)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02a-01 | 06-02a | 1 | REM-03 (env) | integration | `docker exec puppeteer-agent-1 printenv AGENT_URL \| grep -q "192.168"` | ❌ Wave 0 | ⬜ pending |
| 02a-02 | 06-02a | 1 | REM-03 (registry) | integration | `curl -sSf http://localhost:5000/v2/puppet-node/tags/list \| grep -q "latest"` | ❌ Wave 0 | ⬜ pending |
| 02a-03 | 06-02a | 1 | REM-03 (harness) | integration | `python3 -c "import ast; ast.parse(open('/home/thomas/Development/mop_validation/scripts/test_installer_lxc.py').read())"` | ❌ Wave 0 | ⬜ pending |
| 02b-01 | 06-02b | 2 | REM-03a,f | integration | `curl with valid token \| grep "5000"` (manual token required) | ✅ | ⬜ pending |
| 02b-02 | 06-02b | 2 | REM-03a,b,d,f | integration | `python3 .../test_installer_lxc.py 2>&1 \| tail -20` | ❌ Wave 0 | ⬜ pending |
| 02c-01 | 06-02c | 3 | REM-03c | integration | `incus exec mop-test-node -- bash -c "which jq; echo $?"` | ❌ Wave 0 | ⬜ pending |
| 02c-02 | 06-02c | 3 | REM-03b,c,e | integration | `python3 .../test_installer_lxc.py 2>&1 \| grep -E "REM-03e\|REM-03b-nonroot\|PASS\|FAIL"` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `mop_validation/scripts/test_installer_lxc.py` — integration harness covering REM-03a through REM-03f (created in Wave 1, plan 06-02a)
- [ ] `mop_validation/scripts/setup_installer_test_env.sh` — helper: installs podman-compose, jq, registry config inside LXC node
- [ ] Local registry running at `localhost:5000` with `puppet-node:latest` pushed (Wave 1 prerequisite task)
- [ ] `AGENT_URL` set to LAN IP in `puppeteer/.env` and server restarted (Wave 1 prerequisite task)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Node heartbeat visible in dashboard | REM-03d | Requires browser/UI | Log into dashboard → Nodes view → verify new node appears with green status within 60s of installer completion |
| CA trusted by system curl (no -k) | REM-03b | Curl output varies by OS | `incus exec mop-test-node -- curl -sSf https://<SERVER_IP>:8001/health` returns 200 without -k |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5 minutes (integration)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
