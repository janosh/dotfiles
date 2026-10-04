---
name: adversarial-review
description: "Run an adversarial review of code/changes — correctness, tests, performance, conciseness — and action verified findings. Reviews cross-model when the harness exposes another model family, else with your own model. Modifier: same-model (force your own model)."
---

# Adversarial Review

Draft a self-contained adversarial review prompt, launch one or more reviewer subagents on the Step 2 model to execute the review — fanning out across a large diff — then action every finding they return.

## Step 1: Write the review prompt

Give the reviewer enough context to judge the work against the user's intent (and the original plan, if any).

Include the user request, implementation scope, relevant diffs/commits, changed files, plan files, handoff notes, test results, known tradeoffs, and links/paths to resources the reviewer should read.

Explain the decision-making trail: what was tried, what was chosen, why, what was intentionally skipped, and any uncertainty or corners that may have been cut.

Ask the reviewer to assess: correctness (edge cases, integration, error handling); test coverage and assertion strength; performance and efficiency; and code optimality — elegance, conciseness, simplicity. If a plan or spec exists, also verify it's fully and correctly implemented.

Ask for concrete fixes or patches where obvious, stronger tests for weak coverage, and better designs — including significant refactors when the end result would be clearly better (simpler, faster, or more robust), not just small in-place tweaks.

Explicitly task the reviewer with hunting for bloat, overengineering, slop, and non-DRY code: needless abstractions, premature generalization, duplicated logic, dead code, speculative configurability, and defensive cruft. Ask it to call out what to delete, simplify, or rework, not only what is broken.

Make the prompt self-contained, specific, and actionable. Do not hide risks to make the first agent's work look better.

## Step 2: Pick the reviewer model

A different model family catches different bugs, so use one whenever the harness offers it.

- **Several families available** (e.g. Cursor exposing both Claude and GPT subagent models): pick the strongest model from a family other than yours, chosen from the model list the harness actually exposes. Prefer the newest version; never invent or hardcode version names. Prefer fast models: avoid extra-high reasoning variants such as Fable 5 xhigh (too slow for this loop); use medium effort, or at most high in tricky cases.
- **Single family** (e.g. Claude Code, Codex) or `same-model`: review with your own model. Omit the model override so the subagent inherits it, or pass your own model (or its alias) if the harness would otherwise default subagents to a different one.

Report which reviewer model ran and whether the review was cross- or same-model.

## Step 3: Dispatch the reviewer subagent(s)

Launch reviewers on the Step 2 model in read-only mode. Each returns, for its scope, a prioritized list of correctness bugs, test gaps, performance issues, and bloat/overengineering/elegance improvements (including refactor proposals) — each with a concrete fix — plus a plan-completion verdict if a plan exists.

- Use one subagent by default. Partition by feature/directory only when each slice needs deep independent review, shares little cross-cutting context, and serial review clearly costs more than dispatch and aggregation. Use one parallel layer, give each reviewer the shared context plus its slice, then aggregate findings and judge cross-cutting concerns yourself.

Do not let a reviewer's praise substitute for evidence — weight concrete findings over verdicts.

## Step 4: Action every finding

Process every finding the reviewer returns — none may be silently dropped. The reviewer can be wrong, so confirm before acting. For each finding, do exactly one of:

- **Confirm → implement it now.** Verify the finding yourself with concrete evidence. If it holds and the fix is low-risk and behavior-preserving, make the change, add/strengthen the test, or delete the code this session. Don't defer.
- **Can't confirm, disagree, or it's behavior-changing/subjective → report it to the user** with your reasoning, instead of acting on unverified review output, so the user can decide.

Bias toward deleting and simplifying: once you've confirmed a bloat, overengineering, or non-DRY finding, cut the code rather than adding layers, shims, or abstractions. Do not iterate into AI slop.
