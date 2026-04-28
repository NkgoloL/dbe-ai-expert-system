---
description: "Project-wide instructions for Copilot agents working on DBE AI Expert System."
applyTo: ["**/*"]
---

# DBE AI Expert System Agent Guidance

This repository is an Azure AI Expert System prototype. Agents must:

1. Review the repository structure before editing.
2. Respect the user's request and prioritize root `AGENT_INSTRUCTIONS.md` guidance.
3. Always document all design decisions, code changes, and test updates in PR descriptions or commit messages.
4. Add or update tests for any behavior change.
5. Keep all changes minimal, safe, and aligned with the system's Azure-first architecture.
6. If a git workspace is available, create a commit with a descriptive message and push the branch.

Use the root `AGENT_INSTRUCTIONS.md` as the canonical policy for this project.
