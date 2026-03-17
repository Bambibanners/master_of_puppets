---
phase: 27
slug: ci-cd-packaging-distribution
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-17
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (backend)** | pytest (version in requirements.txt) |
| **Framework (frontend)** | vitest (vitest.config.ts) |
| **Config file (backend)** | `pyproject.toml` — `[tool.pytest.ini_options]` |
| **Config file (frontend)** | `puppeteer/dashboard/vitest.config.ts` |
| **Backend quick run** | `cd puppeteer && API_KEY=ci-dummy-key ENCRYPTION_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= DATABASE_URL=sqlite+aiosqlite:///./test.db pytest -x` |
| **Backend full suite** | `cd puppeteer && API_KEY=ci-dummy-key ENCRYPTION_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= DATABASE_URL=sqlite+aiosqlite:///./test.db pytest` |
| **Frontend test run** | `cd puppeteer/dashboard && npx vitest run` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run backend quick run or `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` for workflow file tasks
- **After every plan wave:** Run backend full suite + `cd puppeteer/dashboard && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| CI workflow creation | 01 | 1 | CI triggers + test matrix | smoke | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` | ❌ W0 | ⬜ pending |
| Release workflow creation | 01 | 1 | v* tag → Docker + PyPI | smoke | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"` | ❌ W0 | ⬜ pending |
| Backend tests pass with dummy env | 01 | 1 | pytest CI compatibility | unit | `cd puppeteer && API_KEY=ci-dummy-key ENCRYPTION_KEY=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA= DATABASE_URL=sqlite+aiosqlite:///./test.db pytest` | ✅ | ⬜ pending |
| Frontend tests pass in CI mode | 01 | 1 | vitest non-watch | unit | `cd puppeteer/dashboard && npx vitest run` | ✅ | ⬜ pending |
| Installer rebranding | 02 | 1 | No MoP/Master strings | content | `grep -r "Master of Puppets\|[^a-zA-Z]MoP[^a-zA-Z]" puppeteer/installer/ 2>/dev/null; echo "exit:$?"` | ✅ | ⬜ pending |
| PyPI package builds | 01 | 1 | axiom-sdk wheel+sdist | smoke | `pip install build && python -m build && ls dist/` | ✅ | ⬜ pending |
| Docs update | 02 | 1 | curl one-liner documented | content | `python3 -c "c=open('docs/docs/getting-started/enroll-node.md').read(); assert 'installer.sh' in c and 'installer/compose' in c; print('PASS')"` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all application behavior. No new test files needed.

- [x] Verify `pyyaml` available for YAML syntax smoke tests: `python3 -c "import yaml"` (usually pre-installed on ubuntu-latest)

*Existing `puppeteer/tests/` and `puppeteer/dashboard/src/views/__tests__/` cover all application behavior. This phase adds workflow files (validated by syntax check) and docs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PyPI Trusted Publisher configured | Release workflow succeeds on v* tag | Requires one-time manual setup at pypi.org + test.pypi.org before first tag push | 1. Go to pypi.org → project → Publishing → Add Trusted Publisher (org=axiom-laboratories, repo=master_of_puppets, workflow=release.yml, env=pypi). 2. Repeat for test.pypi.org with env=testpypi. 3. Create GitHub environments `testpypi` and `pypi` in repo Settings → Environments |
| GHCR image pushes correctly | Docker release job succeeds | Requires push to verify actual GHCR auth and manifest | Push a v* tag and verify image appears at ghcr.io/axiom-laboratories/axiom |
| Getting-started docs render | curl one-liner is primary path | Browser/markdown rendering | Read updated docs and verify two install paths are presented clearly |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready
