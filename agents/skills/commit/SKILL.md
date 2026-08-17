---
name: commit
description: "Stage, commit, and push changes in the current repository. Modifiers: nv (--no-verify), mine (own edits only), local (no push), amend update-msg|keep-msg (amend HEAD and force-push with lease; update-msg by default)."
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
| `amend` | amend `HEAD`; defaults to `update-msg` |
| `keep-msg` | with `amend`, retain the existing commit message |
| `update-msg` | with `amend`, replace the message to describe the complete amended commit |

## Amend (`/commit amend [update-msg|keep-msg] [mine] [local] [nv]`)

1. Use `update-msg` when neither message submode is given; use `keep-msg` only when explicit, and reject both together.
2. Stage all edits, or only this agent's paths with `mine`; stop if `mine` would include unrelated pre-staged paths.
3. Unless `local`, require an existing upstream and confirm its destination with a dry run before rewriting `HEAD`.
4. With `keep-msg`, use `git commit --amend --no-edit`. With `update-msg`, replace the title and body with a concise message derived from the complete amended commit. Run hooks unless `nv` is present.
5. Unless `local`, run `git push --force-with-lease --dry-run`, confirm the expected branch and remote, then `git push --force-with-lease`. Never use plain `--force`.

## Rules

- Only when user asks (invoking this skill counts)
- Warn before committing if the diff looks unfinished, unpolished, or needlessly bloated
- No debug/commented-out instrumentation
- No force-push or amend unless the user explicitly requests it; invoking `amend` authorizes both for this operation only
- Never stash/reset/checkout others' dirty files
- No upstream → stop; don't invent `-u`
