---
name: fix-ssh-terminal
description: >-
  Recover broken Cursor Remote-SSH terminals (empty output/0ms runs/ENOENT zsh)
  and prevent recurrence.
---

# Fix SSH Terminal (Remote)

## When to use

- Shell commands return empty output with `0ms` execution time
- Commands exit `0` but print nothing
- Errors mention `ENOENT spawn zsh`

## Root Cause

Remote host shell/profile mismatch (often `zsh` vs missing `zsh`) or stale remote terminal server state.

## Procedure

1. **Quick reset**
   - Run `Remote-SSH: Kill VS Code Server on Host`
   - Fully restart Cursor and reconnect

1. **Prevent recurrence (remote scope settings)**
   - Set `terminal.integrated.defaultProfile.linux` to `bash`
   - Set Linux bash profile path to `/bin/bash`
   - Do this in **Remote [SSH: host]** scope, not local User scope

   Optional fallback in `settings.json`:

```json
{
  "terminal.integrated.defaultProfile.linux": "bash",
  "terminal.integrated.profiles.linux": {
    "bash": {
      "path": "/bin/bash"
    }
  }
}
```

1. **Last resort (on remote host shell)**
   - SSH into host outside Cursor and kill cursor-server processes:

```bash
ps -ef | grep -i cursor-server | grep -v grep | awk '{print $2}' | xargs -I {} kill -9 {}
```

- Reopen Cursor and reconnect

## While blocked

1. Use file tools to continue non-shell edits.
1. Try `Task` with `subagent_type="shell"` for an isolated terminal.
1. Provide exact manual commands for user to run externally.
