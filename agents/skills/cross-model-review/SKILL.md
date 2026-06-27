---
name: cross-model-review
description: Run a different-model adversarial review of code/changes — correctness, tests, performance, conciseness — and action verified findings.
---

# Cross-Model Review

Draft a self-contained adversarial review prompt, launch one or more reviewer subagents (on a different model family than yours) to execute the review — fanning out across a large diff — then action every finding they return.

## Step 1: Write the review prompt

Write a prompt for another agent to adversarially review the code/changes. Give enough context to judge the work against the user's intent (and the original plan, if there is one).

Include the user request, implementation scope, relevant diffs/commits, changed files, plan files, handoff notes, test results, known tradeoffs, and links/paths to resources the reviewer should read.

Explain the decision-making trail: what was tried, what was chosen, why, what was intentionally skipped, and any uncertainty or corners that may have been cut.

Ask the reviewer to assess: correctness (edge cases, integration, error handling); test coverage and assertion strength; performance and efficiency; and code optimality — elegance, conciseness, simplicity. If a plan or spec exists, also verify it's fully and correctly implemented.

Ask for concrete fixes or patches where obvious, stronger tests for weak coverage, and better designs — including significant refactors when the end result would be clearly better (simpler, faster, or more robust), not just small in-place tweaks.

Explicitly task the reviewer with hunting for bloat, overengineering, slop, and non-DRY code: needless abstractions, premature generalization, duplicated logic, dead code, speculative configurability, and defensive cruft. The goal is lean, clean, optimal code — call out what to delete, simplify, or rework, not only what is broken.

Make the output prompt self-contained, specific, and actionable. Do not hide risks to make the first agent's work look better.

## Step 2: Pick a reviewer model from a different family

A different model family catches different bugs, so the reviewer must NOT share your family.

- Identify your own model family (e.g. OpenAI GPT, Anthropic Claude/Opus, Google Gemini).
- Pick the strongest model from a *different* family, chosen from the model list the current harness actually exposes (e.g. Cursor's subagent model slugs). Prefer the newest available version; never invent or hardcode version names.
- Rough mapping: if you're GPT, review with the latest Opus/Claude; if you're Claude/Opus, review with the latest GPT. If the harness exposes no model override, or no different-family model is available, omit the override and note the review is same-family (or that cross-family dispatch is unavailable).

## Step 3: Dispatch the reviewer subagent(s)

Launch reviewers on the Step 2 model in read-only mode. Each returns, for its scope, a prioritized list of correctness bugs, test gaps, performance issues, and bloat/overengineering/elegance improvements (including refactor proposals) — each with a concrete fix — plus a plan-completion verdict if a plan exists.

- Small diff: one subagent with the Step 1 prompt.
- Large diff (roughly 7+ files, or spanning multiple features/new dirs): partition the diff by feature/dir and launch one reviewer per partition in parallel (one layer, no nested fan-out), each given the shared context plus its slice. Then aggregate and de-duplicate their findings, and judge cross-cutting concerns and overall plan completion (if a plan exists) across partitions yourself.

Do not let a reviewer's praise substitute for evidence — weight concrete findings over verdicts.

## Step 4: Action every finding

Process every finding the reviewer returns — none may be silently dropped. The reviewer can be wrong, so confirm before acting. For each finding, do exactly one of:

- **Confirm → implement it now.** Verify the finding yourself with concrete evidence. If it holds and the fix is low-risk and behavior-preserving, make the change, add/strengthen the test, or delete the code this session. Don't defer.
- **Can't confirm, disagree, or it's behavior-changing/subjective → report it to the user** with your reasoning, instead of acting on unverified review output, so the user can decide.

Bias toward deleting and simplifying: once you've confirmed a bloat, overengineering, or non-DRY finding, cut the code rather than adding layers, shims, or abstractions. The objective is lean, clean code — do not iterate into AI slop.
