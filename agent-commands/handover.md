# Handover

## Goal

Generate `HANDOVER.md` summarizing the session for the next agent. Use when context window fills up or ending complex work.

## Steps

1. **Review:** Scan conversation for key activities.
2. **Generate `HANDOVER.md`** with sections:
   - What We Did
   - Current State (branch, task, blockers)
   - Key Decisions (with rationale—capture *why*)
   - Pitfalls & Lessons Learned
   - Open Questions
   - Next Steps
   - Files Changed
3. **Commit** if appropriate.

## Rules

- Be specific—include file paths, line numbers
- Capture *why* decisions were made, not just *what*
- Note anything surprising or non-obvious
