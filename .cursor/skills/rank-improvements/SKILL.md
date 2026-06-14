---
name: rank-improvements
description: Rank improvement opportunities in changed code, implement the confident ones, and surface judgment calls. Use for review and cleanup.
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
5. Act on findings, don't just list them:
   - Immediately implement any fix you've verified is low-risk and behavior-preserving, regardless of severity.
   - Report (don't auto-apply) high-risk, behavior-changing, design-level, or high-effort items — even Critical ones — each with a recommendation.

## Rules

- Auto-apply confident, low-risk fixes; report the rest — don't make the user re-request obvious wins
- Keep scope to changed code
- Omit empty severity sections
- Apply best judgment on which improvements to implement versus leave undone.
- Prioritize complexity/utility tradeoffs: avoid high-effort or high-maintenance changes unless their value is clearly commensurate.
- Treat long-term maintenance cost as a first-class downside; high-maintenance improvements need especially strong payoff.
