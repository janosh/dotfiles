---
name: address-local-coderabbit-comments
description: Extract CodeRabbit comments for the most recent review round in the active repo and triage them for action.
---

# Address Local CodeRabbit Comments

## When to use

Use this skill when a user asks for:

- current CodeRabbit nitpicks/comments for the active repo
- triaging or addressing the latest CodeRabbit feedback
- the current review round status, not historical rounds

## Quick workflow

1. Identify the target workspace path (usually current repo).
2. Run the helper script with `--stdout`:

```bash
# All comment types from latest review round
python "/Users/janosh/dev/dotfiles/.cursor/skills/address-local-coderabbit-comments/scripts/extract_comments.py" --workspace "/absolute/path/to/repo" --stdout

# Assertive comments only from latest review round
python "/Users/janosh/dev/dotfiles/.cursor/skills/address-local-coderabbit-comments/scripts/extract_comments.py" --workspace "/absolute/path/to/repo" --type assertive --stdout
```

1. Report:

- selected review id/title/timestamp
- source cache file used
- extracted comment count by type
- concise triage summary (file, lines, issue, recommendation)

## Critical behavior

- The extractor always selects the most recent review round for the active workspace.
- It does not fall back to older rounds just because they have more comments.
- If the latest round has zero assertive comments, report zero instead of using older nitpicks.

## Review style guardrails

When acting on extracted comments:

- Verify every comment against the current code before changing anything.
- Treat findings as suggestions, not mandates; reject false positives explicitly.
- Prefer simplification and clarity over defensive complexity.
- If a suggestion conflicts with project conventions, keep the convention and note why.
