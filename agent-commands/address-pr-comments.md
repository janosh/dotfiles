# Address PR Comments

## Goal

Read all bot and reviewer comments on a PR, address them in code, add tests where needed, and mark resolved.

## Steps

1. **Fetch:** `gh pr view <number> --comments` and `gh api repos/{owner}/{repo}/pulls/{number}/comments`
2. **Categorize:**
   - **Bugs/Issues:** Must fix
   - **Suggestions:** Evaluate and apply if sensible
   - **Nitpicks:** Fix all (style, naming, formatting)—quick wins
   - **Questions:** Answer in code or reply if clarification needed
3. **Address each:**
   - Read full context (surrounding code, linked lines)
   - Implement the fix or improvement
   - Add tests if comment reveals missing coverage
   - If you disagree, reply with explanation instead of ignoring
4. **Resolve:** Requires GraphQL (REST API can't resolve threads). Get thread IDs via GraphQL, then: `gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "PRRT_..."}) { thread { isResolved } } }'`
5. **Commit:** Batch related fixes, reference comment in message if helpful

## Rules

- **Don't skip nitpicks**—they're quick wins and show attention to detail
- **Add tests** when a comment reveals untested behavior
- **Reply before dismissing**—if you disagree, explain why. Not rare that bot comments are wrong: outdated limitations from old package versions, unnecessary old browser support, etc. We target latest versions only.
- **Batch commits**—bundle related fixes, don't make one commit per comment unless unrelated
