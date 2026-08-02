---
name: address-local-coderabbit-comments
description: Extract CodeRabbit comments for the most recent review round in the active repo and triage them for action.
---

# Address Local CodeRabbit Comments

## When to use

Use this skill when a user asks for:

- current CodeRabbit nitpicks or main review comments for the active repo
- triaging or addressing the latest CodeRabbit feedback
- the current review round status, not historical rounds

## Mode toggle

Pick one mode before running the helper:

| Mode | Flag | Source | Use when |
| --- | --- | --- | --- |
| Nitpicks (default) | `--mode nitpicks` or omit | `assertiveComments` (usually severity `trivial`) | User asks for nitpicks / assertive / low-prio suggestions |
| Main | `--mode main` | `fileReviewMap` actionable comments (usually `minor`/`major`) | User asks for main / high-priority / actionable review findings |

Do not mix modes in one pass unless the user asks for both; then run twice.

## Quick workflow

1. Identify the target workspace path (usually current repo).
1. Choose mode (table above), then run:

```bash
# Nitpicks (default)
uv run --no-project "/Users/janosh/dev/dotfiles/agents/skills/address-local-coderabbit-comments/scripts/extract_comments.py" --workspace "/absolute/path/to/repo"

# Main / higher-priority actionable comments
uv run --no-project "/Users/janosh/dev/dotfiles/agents/skills/address-local-coderabbit-comments/scripts/extract_comments.py" --workspace "/absolute/path/to/repo" --mode main
```

1. Triage from the printed comments (`file:lines` + body).

`--type all` widens nitpicks; `--json` dumps the full cache-shaped payload (keeps `<details>` bodies).

## Critical behavior

- Defaults: `--mode nitpicks`, nitpick `--type assertive`, compact plain text (details chrome stripped).
- Always use the latest review round for the workspace; never fall back to older rounds or the other mode when the chosen mode is empty.

## Review style guardrails

When acting on extracted comments:

- Verify every comment against the current code before changing anything.
- Treat findings as suggestions, not mandates; reject false positives explicitly.
- Prefer simplification and clarity over defensive complexity.
- If a suggestion conflicts with project conventions, keep the convention and note why.
