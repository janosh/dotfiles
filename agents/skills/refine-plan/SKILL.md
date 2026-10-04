---
name: refine-plan
description: Critique and refine an implementation plan before coding a non-trivial feature or refactor, resolving derivable questions yourself and escalating only genuine unknowns.
---

# Refine Implementation Plan

## Instructions

1. Draft approach: what to build, order, and how pieces connect.
2. Self-critique for vague steps, missing error handling, unstated assumptions, and unclear dependencies.
3. List uncertainties (ambiguous requirements, unknown constraints, open design choices).
4. Resolve every uncertainty you can yourself first — read the code, run things, check docs/history. Dispatch read-only research subagents only when independent unknowns each require deep exploration and serial research clearly costs more than dispatch and synthesis. Only escalate the genuinely undecidable ones (product intent, ambiguous requirements, external constraints).
5. Ask the user numbered questions for those remaining and wait for answers.
6. Revise into concrete steps with explicit edge cases and interfaces.
7. Present the final plan and confirm before implementation.

## Rules

- Planning only — no implementation code yet.
- Batch genuine judgment calls into one round of questions; iterate if answers reveal new gaps.
