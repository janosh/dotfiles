---
name: submit-pr
description: "Prepare branch, commit pending changes, and open a GitHub PR with labels and structured metadata. Use only when the user explicitly asks to open a PR. Modifier: distribute."
---

# Submit PR Flow

Supports `distribute`: subagents may take read-only diff inventory, commit grouping, metadata, or label selection.

## Instructions

1. If on `main`, auto-create a descriptive param-case branch name: max 5-6 words, preferably shorter when clarity is preserved.
2. Review local changes and organize semantic commits in dependency order.
3. Derive PR title and body from the full diff, not the branch name or latest commit, following step 3 of [update-pr-metadata](../update-pr-metadata/SKILL.md).
4. Inspect labels and apply best-fit labels. Use `gh` for the PR and labels workflow.
