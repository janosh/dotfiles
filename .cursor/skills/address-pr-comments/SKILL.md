---
name: address-pr-comments
description: Triage and resolve PR comments from humans and bots, including code/test updates and thread resolution workflow.
---

# Address PR Comments

## When to use

- A PR has unresolved review comments
- You need systematic comment-by-comment remediation

## Instructions

1. Fetch comments via `gh` APIs.
2. Categorize into bugs, suggestions, nitpicks, and questions.
3. Address each with code/test updates or explicit rationale when disagreeing.
4. Resolve review threads through GraphQL where applicable.
5. Batch related fixes into coherent commits.

## Rules

- Do not silently ignore comments
- Add tests when comments expose missing behavior coverage
- Prioritize correctness and high-signal feedback first
