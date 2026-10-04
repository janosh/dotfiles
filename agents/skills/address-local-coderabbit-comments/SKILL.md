---
name: address-local-coderabbit-comments
description: Extract CodeRabbit comments for the most recent review round in the active repo and triage them for action.
---

# Address Local CodeRabbit Comments

## Quick workflow

1. Identify the target workspace path (usually current repo).
1. Run the helper. One call returns the whole round, main comments first:

```bash
uv run --no-project "/Users/janosh/dev/dotfiles/agents/skills/address-local-coderabbit-comments/scripts/extract_comments.py" --workspace "/absolute/path/to/repo"
```

1. Triage from the printed comments (`file:lines` + body).

`--mode main` or `--mode nitpicks` narrows the output (text or JSON); `--json` dumps review metadata plus each comment's raw body (keeps `<details>` blocks).

## Critical behavior

- The default reads every bucket, so an empty result means an empty round. Never re-run with a narrower `--mode` to confirm there is no work.
- Always use the latest review round for the workspace; never fall back to older rounds.
- Caches are per editor and per workspace, and go stale silently. The script searches every VS Code-family editor it finds (Cursor, Code, Insiders, VSCodium, Windsurf, Positron) and picks the newest round across all of them; `--ide-user-dir` overrides and is repeatable.
- The header carries the round's date. If it is not roughly today and the user expected fresh findings, say so with that date instead of reporting the round as current: their editor may be writing to a cache this machine has not synced.

## Review style guardrails

When acting on extracted comments:

- Verify every comment against the current code before changing anything.
- Treat findings as suggestions, not mandates; reject false positives explicitly.
- Prefer simplification and clarity over defensive complexity.
- If a suggestion conflicts with project conventions, keep the convention and note why.
