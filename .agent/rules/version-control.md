---
trigger: always_on
---

# Change Control & Git Standards (Software Engineering)
- **Commit Philosophy:** "Little and Often."
    - **Atomic Commits:** Each commit should do ONE thing (e.g., "Fix retry logic" should not be in the same commit as "Update README").
    - **Broken Code:** Never commit code that breaks the build or fails syntax checks. Use `git stash` if you need to switch contexts.
- **Branching Strategy:**
    - Assume a feature-branch workflow. Create branches named `feature/description` or `fix/issue-name` (e.g., `feature/api-rate-limiter`).
- **Conventional Commits:**
    - Strictly follow the Conventional Commits specification.
    - Structure: `<type>: <description>`
    - Types:
        - `feat:` New feature
        - `fix:` Bug fix
        - `docs:` Documentation only
        - `chore:` Maintenance (e.g., updating dependencies)
    - *Example:* `feat: add exponential backoff to API client`
- **Safety:**
    - **PRE-COMMIT CHECK:** Scan for API keys, passwords, or connection strings. If found, DO NOT COMMIT. Replace with environment variable references (e.g., `os.getenv('DB_PASSWORD')`).