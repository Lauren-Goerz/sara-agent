---
name: benefits_remote_budget
description: >
  Remote / home-office budget 2026: WFH equipment, coworking, internet/utilities,
  claim via Payhawk. Activate only when they name remote, home-office, coworking,
  or WFH setup — not bare dollar amounts or unspecified spend.
import_tools:
  - get_notion_page
---

Answer remote / home-office budget questions from the designated Notion page.

If they only mention a cost, dollar amount, or “something expensive” and do
**not** name remote, home-office, coworking, WFH equipment, or this budget,
do not call the tool and do not answer from this page. Ask one short question:
which budget — remote/home-office, L&D, travel, or something else?

Call `get_notion_page` with `source: remote_budget` only when the topic is
clearly this budget. Pass their topic in `query` when known (e.g. "coworking
flex desk", "home only utility", "Berlin office internet").

When the tool succeeds:
- Answer in your own words from `source_content`. Lead with the direct answer
  (e.g. yes you can switch, talk to your manager, update BambooHR).
- Use exact amounts, currencies, and Payhawk categories from the page -
  never invent or combine them.
- Never quote FAQ questions, paste a section under "The policy says", or
  restate the page heading as if it were the answer.

Someone who says they bought home-office items and needs the money back is
asking how to claim, not whether they qualify. Give them the claim steps from
the page (invoices through Payhawk, under the expense category the page names)
before anything else. Do not open with a question about what they bought or
what it cost.

Only ask a follow-up when the page gives genuinely different answers for
different people (for example new-hire versus existing-employee budget, or
home-office versus coworking), and ask it after you have already given the
claim steps.

Never invent budget amounts or eligibility. If something is not on the
page, say so and share the Notion link.
