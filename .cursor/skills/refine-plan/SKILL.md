---
name: refine-plan
description: Critique and refine an implementation plan before coding, resolving derivable questions yourself and escalating only genuine unknowns.
---

# Refine Implementation Plan

## When to use

- Before implementing a non-trivial feature or refactor
- When requirements or approach still have gaps

## Instructions

1. Draft approach: what to build, order, and how pieces connect.
2. Self-critique for vague steps, missing error handling, unstated assumptions, and unclear dependencies.
3. List uncertainties (ambiguous requirements, unknown constraints, open design choices).
4. Resolve every uncertainty you can yourself first — read the code, run things, check docs/history; for several independent unknowns, dispatch read-only research subagents in parallel and synthesize their answers. Only escalate the genuinely undecidable ones (product intent, ambiguous requirements, external constraints).
5. Ask the user numbered questions for those remaining; wait for answers before coding.
6. Revise into concrete steps with explicit edge cases and interfaces.
7. Present the final plan and confirm before implementation.

## Rules

- Planning only — no implementation code yet.
- Replace hand-wavy steps with precise actions.
- Don't ask what you can derive; batch only genuine judgment calls and iterate if answers reveal new gaps.

## Outcome

An agreed implementation plan ready to execute without guesswork.
