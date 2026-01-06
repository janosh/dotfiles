# Improve Uncommitted Changes

## Goal

Review, refactor, and improve uncommitted (working directory) changes to make them robust, readable, and concise before committing.

## Modes

- **Default:** Analyze and fix issues
- **Audit only:** Add "audit only" to get a read-only analysis without applying fixes

## Steps

1. **Review:** Analyze all uncommitted files for bugs, performance issues, and code smells.
2. **Identify:** Look for boilerplate reduction, refactoring potential, and cleanup opportunities.
3. **Prioritize:** Rank issues by impact (High/Medium/Low).
4. **Improve** (skip if audit only):
   - If confident: Implement fixes and refactoring immediately
   - If unsure: Ask clarifying questions (bundle them at the end)

## Rules

- **Behavior Preservation:** Ensure the logic remains correct
- **Priority:** Focus on high-impact cleanups (DRY, readability) first
- **Quality First:** Make code robust and readable before committing

## Outcome

Clean, refactored code that's ready for commit with reduced boilerplate and improved maintainability.
