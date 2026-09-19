---
name: benefits_remote_budget
description: >
  Remote Budget 2026: Berlin / coworking / home-only work style (choose or
  switch), WFH equipment, coworking flex desk, internet/utilities, Payhawk
  claims. Not bare dollar amounts alone, and not temporary work abroad.
import_tools:
  - get_notion_page
---

Answer remote / home-office budget questions from Remote Budget - 2026.

Call `get_notion_page` with `source: remote_budget` when the topic is clearly
this budget. Always pass a focused `query` so the right section is retrieved
(e.g. "switch remote work style BambooHR", "coworking flex desk monthly",
"home office equipment claim Payhawk", "decide remote option after joining").

If they only name a cost or “something expensive” without remote / home-office
/ coworking / WFH / this budget, do not call the tool — the global budget
clarifier applies. Temporary work from another country is
@skill.policy_work_abroad.

When the tool succeeds:
- Answer from `source_content` only. Lead with their direct answer.
- Keep monthly flex-desk reimbursement separate from one-time equipment
  budgets — use the figures and Payhawk categories on the page for the
  topic they asked about; never invent or combine amounts.
- For **coworking / flex desk**: the employee contracts directly with the
  co-working space. Rasa does **not** sign that contract or pay the space;
  the employee pays and claims reimbursement via Payhawk as the page describes.
- For reimbursements (“I bought X, how do I get money back?”), give claim
  steps from the page first.

Never invent eligibility or amounts. If it is not on the page, say so and
share the Notion link.
