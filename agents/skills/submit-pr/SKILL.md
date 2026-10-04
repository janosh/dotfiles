---
name: submit-pr
description: Prepare branch, commit pending changes, and open a GitHub PR with labels and structured metadata. Use only when the user explicitly asks to open a PR. Optional `distribute` mode delegates independent preparation to subagents.
---

# Submit PR Flow

## Mode toggle

- Direct (default): keep work in the current agent.
- `distribute`: use when requested or when one parallel layer of independent preparation is worthwhile. Delegate read-only diff inventory, commit grouping, metadata, or label selection; the parent reconciles findings and performs every write. If no safe useful split exists, explain and use Direct.

## Instructions

1. If on `main`, auto-create a descriptive param-case branch name: max 5-6 words, preferably shorter when clarity is preserved.
2. Review local changes and organize semantic commits in dependency order.
3. Derive PR metadata from the full diff, not the branch name or latest commit.
   - Title: one line, ~70 characters, so it does not wrap in the GitHub PR UI. Name the primary change; put the rest of the inventory in the body. Do not catalog subsystems, datasets, or follow-on fixes in the title.
   - For large multi-purpose PRs, still pick 1-2 concrete primary changes rather than a vague umbrella description.
   - Use literal, implementation-specific language. Never use vague LLM packaging such as “harden,” “strengthen,” “improve,” “enhance,” “streamline,” “robust,” or “load-bearing.” Prefer “Initialize background tabs, protect dirty buffers, and bound shared dashboard plots” over “Harden background tab and dashboard safety.”
   - Describe every material change as a concise component/mechanism/effect bullet. Include impact, breaking changes, and migration only when applicable; omit empty boilerplate.
   - Never include `Test plan` or `Verification` sections; CI already exposes the authoritative check state.
   - Do not use Conventional Commit prefixes such as `feat:` or `fix:`.
4. Inspect labels and apply best-fit labels. Use `gh` for the PR and labels workflow.
