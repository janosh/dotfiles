---
name: submit-pr
description: Prepare branch, commit pending changes, and open a GitHub PR with labels and structured metadata.
disable-model-invocation: true
---

# Submit PR Flow

## When to use

- User explicitly asks to open a PR

## Instructions

1. Ensure current branch is not `main`.
2. If on `main`, auto-create a descriptive param-case branch name:
   - max 5-6 words
   - preferably shorter when clarity is preserved
3. Review local changes and organize semantic commits in dependency order.
4. Create PR with descriptive title/body (no `feat:`/`fix:` prefixes).
5. Inspect labels and apply best-fit labels.

## Rules

- Use `gh` for PR and labels workflow
- Keep commit and PR messaging concise and descriptive
