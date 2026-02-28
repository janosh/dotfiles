---
name: initialize-long-session
description: Bootstrap persistent files for multi-session project execution and progress tracking.
disable-model-invocation: true
---

# Initialize Long-Running Session

## When to use

- User asks to set up long-running, multi-session project workflow

## Instructions

1. Derive feature list from user requirements and order by dependency.
2. Create `features.md` with checkbox items.
3. Create `claude-progress.txt` with initial session entry.
4. Optionally create `init.sh` for environment setup commands.
5. Create baseline project structure and begin first unchecked feature.

## Rules

- Keep feature list granular and testable
- Work one feature at a time after initialization
- Maintain runnable project state at session boundaries
