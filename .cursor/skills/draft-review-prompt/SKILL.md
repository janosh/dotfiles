---
name: draft-review-prompt
description: Write a prompt for a second adversarial agent to review, test, and polish a first agent's code. Use when handing off work for independent review.
---

# Draft Review Prompt

## Instructions

Write a prompt for another agent to adversarially review the first agent's code. The prompt should give enough context for the reviewer to judge whether the implementation fits the user's needs and the original plan.

Include the user request, implementation scope, relevant diffs/commits, changed files, plan files, handoff notes, test results, known tradeoffs, and links/paths to resources the reviewer should read.

Explain the decision-making trail: what was tried, what was chosen, why, what was intentionally skipped, and any uncertainty or corners that may have been cut.

Ask the reviewer to verify plan completion first, then review correctness, edge cases, integration behavior, tests, conciseness, code quality, and bloat.

Ask for concrete fixes or patch suggestions where obvious, stronger tests for weak coverage, and likely next features or follow-up improvements future users will need because of this work.

Make the output prompt self-contained, specific, and actionable. Do not hide risks to make the first agent's work look better.
