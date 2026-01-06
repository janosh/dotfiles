# Refine Implementation Plan

## Goal

Before writing any code, critically review your own implementation plan. Identify gaps, ambiguities, and missing details. Ask clarifying questions until you have a solid, precise plan that addresses all requirements.

## Steps

1. **Draft plan:** Outline your intended approach—what you'll build, in what order, and how components connect.
2. **Self-critique:** Review your plan for:
   - Vague or hand-wavy steps ("handle edge cases", "add validation", "make it robust")
   - Missing details (error handling, state management, data flow)
   - Unstated assumptions about requirements or existing code
   - Dependencies between steps that aren't explicit
   - Steps that could be broken down further
3. **Identify gaps:** List anything you're uncertain about:
   - Ambiguous requirements
   - Unknown constraints (performance, compatibility, existing patterns)
   - Design decisions that could go multiple ways
4. **Ask questions:** Present your gaps to the user as a numbered list. Wait for answers before proceeding.
5. **Revise plan:** Incorporate answers into a refined plan with:
   - Concrete, actionable steps (no vague language)
   - Clear order of implementation
   - Explicit handling of edge cases and errors
   - Defined interfaces between components
6. **Confirm:** Present the final plan and ask if anything is missing before starting implementation.

## Rules

- **No coding yet:** This is planning only. Don't write implementation code.
- **Be specific:** Replace vague steps with precise actions.
- **Question assumptions:** If you're assuming something about requirements, ask.
- **Batch questions:** Collect all uncertainties and ask them together.
- **Iterate if needed:** If answers reveal new gaps, ask follow-up questions.

## Outcome

A detailed, unambiguous implementation plan that both you and the user agree covers all requirements—ready to execute without guesswork.
