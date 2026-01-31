# Debug

## Goal

Investigate and fix bugs **autonomously**. Collect all data yourself—don't ask the user to run commands or provide logs.

## Mindset

You have terminal, browser, and browser console. Use them. Solve it without asking for help except when you genuinely need human input (credentials, external access, domain expertise, or 3+ failed hypotheses with no progress).

## Steps

1. **Reproduce:** Run failing test/code, start dev server, open browser, trigger the bug, check console for errors.
2. **Gather:** Add `console.log`/`print`, check network tab, inspect element state, read stack traces, check recent git changes.
3. **Isolate:** Binary search (comment out code halves), check if bug exists on `main`, find exact line where behavior diverges.
4. **Hypothesize → Test:** Form theory, predict what you'd see, make minimal change to confirm/refute, repeat until root cause found.
5. **Fix:** Smallest change that fixes it, remove all debug instrumentation, verify fix works.
6. **Prevent:** Add regression test, check for similar bugs elsewhere (`/fix-similar`).

## Rules

- **Don't ask for logs**—collect them yourself
- **Don't ask "can you try X"**—try it yourself
- **Don't give up early**—iterate until solved
- **Clean up**—no debug code in final fix
