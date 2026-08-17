---
name: submit-pr
description: Prepare branch, commit pending changes, and open a GitHub PR with labels and structured metadata. Optional `distribute` mode delegates independent preparation to subagents.
disable-model-invocation: true
---

# Submit PR Flow

## When to use

- User explicitly asks to open a PR

## Mode toggle

- Direct (default): keep work in the current agent.
- `distribute`: use when requested or when one parallel layer of independent preparation is worthwhile. Delegate read-only diff inventory, commit grouping, metadata, or label selection; the parent reconciles findings and performs every write. If no safe useful split exists, explain and use Direct.

## Instructions

1. Ensure current branch is not `main`.
2. If on `main`, auto-create a descriptive param-case branch name:
   - max 5-6 words
   - preferably shorter when clarity is preserved
3. Review local changes and organize semantic commits in dependency order.
4. Derive PR metadata from the full diff, not the branch name or latest commit.
   - Make the title a compact inventory of the affected components and observable changes so readers can predict the diff before opening it. For large multi-purpose PRs, name the major areas and changes directly instead of collapsing them into vague umbrella language.
   - Use literal, implementation-specific language. Never use vague LLM packaging such as “harden,” “strengthen,” “improve,” “enhance,” “streamline,” “robust,” or “load-bearing.” Prefer “Initialize background tabs, protect dirty buffers, and bound shared dashboard plots” over “Harden background tab and dashboard safety.”
   - Describe every material change as a concise component/mechanism/effect bullet. Include impact, breaking changes, and migration only when applicable; omit empty boilerplate.
   - Never include `Test plan` or `Verification` sections; CI already exposes the authoritative check state.
   - Do not use Conventional Commit prefixes such as `feat:` or `fix:`.
5. Inspect labels and apply best-fit labels.

## Rules

- Use `gh` for PR and labels workflow
- Keep commit and PR messaging concise and descriptive
