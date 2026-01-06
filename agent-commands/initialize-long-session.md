# Initialize Long-Running Session

## Goal

Set up scaffolding for a multi-session project so future agent sessions can pick up where previous ones left off.

## Context

Long-running agent tasks fail because each session starts fresh with no memory. This command creates persistent state files that subsequent sessions can read to understand project progress.

## Steps

1. **Understand the task:** Parse the user's project description to identify all required features.
2. **Create features.md:** Write a checklist of all features, ordered by dependency (foundational items first).

   ```markdown
   # Features

   - [ ] Feature 1 description
   - [ ] Feature 2 description
   ...
   ```

3. **Create claude-progress.txt:** Initialize the progress log with session 1 entry.

   ```markdown
   # Claude Progress Log

   ## Session 1 - YYYY-MM-DD HH:MM
   - Initialized project scaffolding
   - Created features.md with N features
   - Next: [first feature to work on]
   ```

4. **Create init.sh (optional):** If the project needs setup commands (install deps, start dev server), write them here.
5. **Set up project structure:** Create initial directories, config files, and boilerplate.
6. **Git commit:** Commit all scaffolding files with message "Initialize long-running agent scaffolding".
7. **Begin first feature:** Start working on the first unchecked feature in features.md.

## Rules

- **Comprehensive feature list:** Break down the task into granular, testable features.
- **Dependency order:** List features so earlier ones don't depend on later ones.
- **One feature per session:** After setup, work on only ONE feature before ending.
- **Clean state:** Leave the project runnable after each session.

## Output Files

| File                  | Purpose                                   |
| --------------------- | ----------------------------------------- |
| `features.md`         | Checkbox list of all features with status |
| `claude-progress.txt` | Session-by-session log of work done       |
| `init.sh`             | Optional setup script for environment     |
