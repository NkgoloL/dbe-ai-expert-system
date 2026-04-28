# Agent Instructions for DBE AI Expert System

This repository contains an Azure-based AI expert system prototype. Agents working on this project must follow these rules for every request.

## Core Behavior
1. Review the repository structure and file contents before making changes.
2. Use the root `AGENT_INSTRUCTIONS.md` and `.github/copilot-instructions.md` as the canonical policy.
3. Prioritize safe, minimal changes that preserve the Azure-first architecture.
4. Always document code changes clearly in commit messages, PR descriptions, and README updates.
5. Add or update tests for any behavior change.
6. If the environment supports git, commit changes with a descriptive message and push the branch.

## How to Use This Agent
- Prefer explicit file edits over broad changes.
- If a user asks for improvements, propose the most practical architecture and implementation refinements.
- For API or orchestration work, validate changes with tests when possible.
- Keep project dependencies and packaging consistent.

## Audit and Reporting
- Whenever you make a change, record what changed and why.
- Update documentation to reflect new capabilities, especially in `README.md`.
- Use the existing `/audits/` reports as examples for audit-style summaries.

## Agent Hooks
- Before editing, confirm the top-level scope (code, infra, docs, tests).
- After editing, verify the project still builds or that tests are added.
- If a commit/push step is available, include it in the final workflow.
