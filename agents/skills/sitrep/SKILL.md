---
name: sitrep
description: "Report progress since the user's previous prompt: elapsed time, accomplishments, open items, new findings, and highest-value next steps. Use for a sitrep or progress update since their last message."
---

# Sitrep

## Instructions

1. Report from the most recent human prompt before this request, including a previous sitrep. Ignore tool messages, automated wakeups, and other agents' messages. Use the current conversation unless the user names another agent/task; then read its available history and status.
2. Start with **Since your last prompt: <elapsed time>.** Calculate wall-clock time from that prompt's timestamp to now using conversation metadata, session logs, or clock tools; format it as `45s`, `18m`, or `2h 10m`. Never use this request's timestamp, message counts, file modification times, or invented times. If the prior prompt or timestamp is unavailable, start with **Since your last prompt: elapsed time unavailable.**, briefly explain why, and continue.
3. Use conversation/tool evidence and only necessary read-only checks. Distinguish verified completion from attempted, running, planned, or unverified work. Include older unresolved items only if they still block the objective; label them carried over.
4. Follow with four bullets. Aim for 100–200 words total, less when little changed. Rank by impact, avoid repetition, and say `None` for empty categories. Never invent entries.
   - **Accomplished:** Completed outcomes since the prior prompt, with relevant verification results.
   - **Open:** Unfinished commitments, ongoing work, blockers, and decisions or input needed; state required user actions explicitly.
   - **New findings:** Facts changing the approach, risk, or expected result; mark hypotheses unverified.
   - **Next:** One to three highest-value actions in priority order, with brief reasons. Suggest new opportunities only when supported by findings and relevant to the goal.
5. Do not launch work to fill the report. Continue already-running, authorized work after the update unless the user asks to stop.
