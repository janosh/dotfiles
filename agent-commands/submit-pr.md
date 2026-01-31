# Submit PR Flow

## Goal

Automate the process of ensuring a clean branch, committing changes, and creating a GitHub Pull Request.

## Steps

1. **Branch Check:** Ensure you are on a feature branch (not `main`).
    - If on `main`, ask to create a new branch with a param-cased short descriptive name.
2. **Review Changes:** Review all uncommitted changes.
3. **Commit:**
    - Group related changes into semantic commits.
    - Order commits logically (dependencies first).
    - Format: Short descriptive message (no feat/fix prefixes) + 2 newlines + detailed list (`- ...`).
4. **Create PR:**
    - Use `gh pr create`.
    - Generate a descriptive title and body based on the commit messages.
    - **No** `feat:`/`fix:` prefixes in the title.
5. **Labels:** Check available labels (`gh label list`) and apply the most fitting ones to the PR.
    - Same when opening issues with `gh issue create`.

## Tools

- Use the GitHub CLI (`gh`).
