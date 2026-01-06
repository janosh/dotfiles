# Review Branch

## Goal

Perform a thorough code review of the current feature branch focusing on architecture, correctness and style. Scope: This reviews the **entire branch diff vs main**. If branch is large, review commit-by-commit.

## Steps

1. **Review:** Analyze the diff between the current branch and `main`. Run `git log --oneline main..HEAD` and `git diff main --stat` to understand scope.
2. **Identify:** Analyze `git diff main` for:
    - Potential bugs
    - Performance bottlenecks
    - Code smells / Verbosity
3. **Rank:** Prioritize findings.
4. **Fix:**
    - If confident: Implement the fixes immediately.
    - If unsure: Ask clarifying questions (bundle them at the end).

## Outcome

Make the codebase robust, readable, and concise.
