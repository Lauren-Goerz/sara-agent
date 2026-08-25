---
name: lookup_remote_budget
description: >
  Remote Budget 2026: home-office equipment, coworking/flex desks, internet
  or utility allowances, Payhawk categories, remote-work styles, and
  part-time/intern rules. Not general benefits, L&D, travel, laptop repairs,
  or Berlin-office operations.
---

Answer remote / home-office budget questions from the designated source.
Call `get_remote_budget_guidance` for every request - pass their topic in
`query` when known (e.g. "coworking flex desk", "home only utility",
"Berlin office internet").

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.
- Use exact amounts, currencies, and Payhawk categories from the page -
  never invent or combine them.
- Always say this guidance is the policy as of *August 11, 2026*, and ask
  them to double-check the formal page for any updates:
  <https://app.notion.com/p/rasa/Remote-Budget-2026-fb07ed3e076f4096a15a1d4fc95091ed|Remote Budget - 2026>

Never invent budget amounts or eligibility. If something is not in
source_content, say so and share the Notion link. If `used_fallback` is
true, still treat source_content as the approved snapshot for that date.
