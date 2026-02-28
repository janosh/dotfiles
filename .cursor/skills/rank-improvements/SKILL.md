---
name: rank-improvements
description: Produce a prioritized, read-only list of improvement opportunities in current changes. Use for planning and triage.
---

# Rank Improvement Ideas

## When to use

- You want a punch list before implementation
- You need prioritized review output for changed code

## Instructions

1. Analyze in this order:
   - Uncommitted changes
   - Branch diff vs `main`
2. Find opportunities in correctness, robustness, simplification, performance, readability, and maintainability.
3. Rank findings by severity: Critical, High, Medium, Low.
4. For each finding include:
   - file/location
   - problem summary
   - concrete fix suggestion

## Rules

- Read-only unless user asks to implement
- Keep scope to changed code
- Omit empty severity sections
