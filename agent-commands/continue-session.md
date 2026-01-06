# Continue Session

## Goal

Resume work on a long-running project by reading existing state, implementing the next feature, and updating progress.

## Context

This command is for sessions after the initial setup. It reads the scaffolding files created by `/initialize-long-session` to understand what's been done and what's next.

## Steps

1. **Orient yourself:**
   - Run `pwd` to confirm working directory.
   - Read `claude-progress.txt` to see what previous sessions accomplished.
   - Run `git log --oneline -10` to see recent commits.
   - Read `features.md` to see the full feature list and current status.

2. **Identify next task:** Find the first unchecked `- [ ]` item in features.md.

3. **Run init.sh (if exists):** Execute any setup commands to get the dev environment running.

4. **Implement ONE feature:**
   - Focus exclusively on the identified feature.
   - Write tests if applicable.
   - Verify the feature works end-to-end.

5. **Update features.md:** Change `- [ ]` to `- [x]` for the completed feature.

6. **Update claude-progress.txt:** Append a new session entry:

   ```markdown
   ## Session N - YYYY-MM-DD HH:MM
   - Implemented [feature name]
   - [Other notable changes]
   - Next: [next unchecked feature or "All features complete"]
   ```

7. **Git commit:** Commit all changes with a descriptive message about what was implemented.

8. **Verify clean state:** Ensure the project runs without errors before ending.

## Rules

- **Read before acting:** Always read progress files and git log first.
- **One feature only:** Do not attempt multiple features in one session.
- **No skipping:** Work on features in order unless blocked.
- **Update state:** Always update both features.md and claude-progress.txt.
- **Test thoroughly:** Verify the feature works before marking complete.
- **Clean commits:** Each session should end with a commit.

## Completion Check

If all features in features.md are checked `[x]`:

1. Update claude-progress.txt with "Project complete" entry.
2. Run final verification of all features.
3. Inform the user the project is ready for review.
