---
name: cleanup
description: "Repository housekeeping: worktrees removes stale branches/worktrees after verifying preservation; wrap-up commits and pushes ready work, then proposes deleting, trashing, or date-archiving leftovers. Not for code refactoring."
---

# Cleanup

The keyword after `/cleanup` selects the mode; default to `worktrees`.

| Invocation | Workflow |
| --- | --- |
| `/cleanup worktrees` | Delete inactive, redundant branches/worktrees; offer recovery or a PR for useful unmerged work. |
| `/cleanup wrap-up` | Commit and push ready work, then suggest cleanup of leftovers. |
| `/cleanup wrap-up local` | Same, without pushing. |

## Routing

1. Read and follow only the selected workflow: [worktrees](references/worktrees.md) or [wrap-up](references/wrap-up.md).
2. `local`, `mine`, and `nv` apply only to `wrap-up`. `audit` or `dry-run` makes either mode read-only: inspect and recommend without committing, pushing, deleting, moving, or modifying files.
3. For unknown/conflicting modes or commit modifiers without `wrap-up`, stop before acting and ask which supported invocation the user intends.
4. Honor previously approved actions and paths. Distinguish completed actions from pending recommendations; preserve active or unverified work.
