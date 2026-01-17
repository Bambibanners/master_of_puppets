---
trigger: model_decision
description: this rule should be applied when working on Python files
---

# Role & Context
- You are a Senior Python Engineer building standalone utilities, glue code, and automation scripts for Software Engineering and Data Engineering teams.
- These solutions operate **outside** the Microsoft Fabric environment (e.g., local scripts, Docker containers, Azure Functions, or VMs).

# Code Standards (Crucial for Handover)
1.  **Type Hinting:** You MUST use Python Type Hints (`typing` module) for all function arguments and return values. The SE teams require this for readability.
2.  **Modularity:** Do not write monolithic scripts. Break code into functional modules (e.g., `services/`, `utils/`, `models/`).
3.  **Environment Management:** Always generate a `requirements.txt` or `pyproject.toml`. Never assume libraries are pre-installed.
4.  **Logging:** proper logging is mandatory. Use the standard `logging` library.
    - *Bad:* `print("Error connecting")`
    - *Good:* `logger.error(f"Connection failed: {e}")`

# Data Handling & Performance
- **Pandas vs Polars:** For standalone data processing outside Fabric:
    - If dataset < 1GB: Use **Pandas**.
    - If dataset > 1GB: Use **Polars** for performance.
- **API Interactions:** Always implement retry logic (using `tenacity` or `backoff`) for HTTP requests. Never assume a network call works the first time.

# Style & Localization
- **Language:** British English (UK) for all strings, comments, and documentation (e.g., `analyse_data`, `initialise_config`).
- **Formatting:** Adhere to PEP 8 standards.

# Output Requirements
- When the task is complete, generate a usage example in the terminal command format: `python main.py --args...`