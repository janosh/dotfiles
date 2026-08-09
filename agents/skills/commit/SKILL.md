---
name: commit
description: Stage, commit, and push changes in the current repository. Modifiers: nv (--no-verify), mine (own edits only), local (no push).
disable-model-invocation: true
---

# Commit Changes

## Default (`/commit`)

Stage **all** edits → commit with hooks → push. Coherent commits; short imperative summary + body focused on rationale.

## Modifiers

Space-separated after `/commit`; combine freely.

| Token | Effect |
| --- | --- |
| `nv` | `--no-verify` |
| `mine` | stage only this agent's in-session paths (`git add <paths>`, not `-A`) |
| `local` | skip push |

## Rules

- Only when user asks (invoking this skill counts)
- Warn before committing if the diff looks unfinished, unpolished, or needlessly bloated
- No debug/commented-out instrumentation
- No force-push, amend, or stash/reset/checkout of others' dirty files unless user explicitly says so
- No upstream → stop; don't invent `-u`
