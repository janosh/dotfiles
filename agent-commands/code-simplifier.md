# Code Simplifier

## Goal

A working solution exists. Your job is to make it as clean, concise, elegant, and idiomatic as possible without changing behavior.

## Steps

1. **Scan:** Review all changed/new code (on the branch and/or uncommitted) for bloat, redundancy, and needless complexity.
2. **Identify:**
   - Dead or unused code (imports, variables, functions, parameters)
   - Overly verbose patterns that have simpler idiomatic alternatives
   - Duplicated logic that can be consolidated
   - Low-quality code (poor naming, unclear intent, missing types/docs)
   - Defensive code that guards against impossible states
3. **Simplify:**
   - Remove dead code and unnecessary abstractions
   - Replace verbose patterns with idiomatic equivalents
   - Consolidate duplicated logic (DRY)
   - Flatten unnecessary nesting
   - Use language/framework features that reduce boilerplate
4. **Improve:**
   - Add missing types and minimal docstrings where unclear
   - Rename variables/functions for clarity
   - Make error handling robust but not paranoid
5. **Ask:** If unsure whether something is dead code or has hidden uses, ask before deleting.

## Rules

- **Preserve Behavior:** Working code must stay working. Run tests if available.
- **Minimal Changes:** Don't refactor unrelated code. Stay focused on the task at hand.
- **Idiomatic First:** Prefer language/framework conventions over clever solutions.
- **When in Doubt, Ask:** If a piece of code seems unused but might have side effects or external consumers, ask before removing.

## Outcome

Lean, readable code that does exactly what it did before—just better.
