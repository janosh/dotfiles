# Commit Changes

## Goal

Commit local changes in logical, well-described chunks. If in doubt whether to split or combine, prefer fewer larger commits over many smaller ones.

## Steps

1. **Review:** Run `git diff` to see all uncommitted changes.
2. **Chunk:** Group related changes into logical units. Each commit should contain as many coherent changes as possible.
3. **Stage:** Use `git add -p` for partial staging if a file has multiple unrelated changes.
4. **Message:** Write a descriptive commit message:
   - **Summary:** Short, imperative (50 chars max). No prefixes like `feat:`/`fix:`.
   - **Body:** Optional. Add after 2 blank lines for complex changes. Use `-` bullets.

## Rules

- Don't commit commented-out code, instrumentation or debug statements
- Avoid "fix typo" commits—amend instead if not yet pushed
- If already pushed, err on the side of not amending unless you are sure the commit is wrong
- Only commit when explicitly asked—don't auto-commit on subsequent prompts
