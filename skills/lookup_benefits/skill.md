---
name: lookup_benefits
description: >
  Employer benefits and perks - gym membership, wellness, fitness,
  equipment stipend, parental-adjacent perks listed on Benefits &
  Perks 2026, health/wellbeing allowances, and "what benefits do we get".
  Activate for gym, ClassPass, wellbeing, perks, employee benefits, or
  similar. Do NOT activate for learning & development, education days,
  L&D / learning budget, courses, or training budget
  (lookup_learning_development). Do NOT activate for leave balances
  (leave_check), vacation/sick/ parental leave process (leave_vacation /
  leave_sick / leave_parental), company values, travel insurance /
  business-trip cover (policy_travel_insurance), business travel
  booking/spend rules (policy_business_travel), remote / home office
  budget (lookup_remote_budget), or general Notion policy search unless
  the ask is clearly a benefit/perk from this page.
---

Answer questions about Rasa employer benefits and perks from the designated
Notion page. Call `get_benefits_and_perks` for every request - pass their
topic in `query` when known (e.g. "gym membership").

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.
- Use exact amounts, eligibility, and any country notes from the page.
- Always finish with:
  <https://app.notion.com/p/rasa/Benefits-Perks-2026-bd1165c5ece74392917d3b3eaffb4388|Benefits & Perks 2026>

Never invent, estimate, or combine benefit amounts. If something is not on
the page, say so and share the Notion link (and People Ops if needed). If the
page is unavailable, share the same link and do not guess.
