# Documentation Standards

**Trigger:** ALWAYS apply this rule when making changes to implementation, architecture, or installation flows.

## Core Principle
"Assume the project is being handed over to a new developer, or a brand new user, every time you update the docs."

## Requirements
1.  **Synchronization:** Code changes MUST be accompanied by documentation updates in the same PR/Task. Never leave docs "for later".
2.  **Zero Assumptions:** Do not assume the user knows about previous context, environment variables on your local machine, or prior discussions. Explicitly state prerequisites.
3.  **Dual-Path Coverage:** If multiple ways exist to do something (e.g., Loader vs. Manual), DOCUMENT BOTH with equal fidelity.
4.  **Verification:** When documenting commands, verify they work. If a command typically fails (e.g. strict firewall), document the troubleshooting steps immediately below it.
5.  **Artifacts:** Update `task.md`, `architecture_hypothesis.md`, and `walkthrough.md` to reflect the current reality, not the historical intent.
