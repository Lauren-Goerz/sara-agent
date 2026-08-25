---
name: lookup_benefits
description: >
  Employer benefits and perks from Benefits & Perks 2026: gym, ClassPass,
  wellness, fitness, equipment, and health/wellbeing allowances. Not L&D,
  leave, travel insurance, or remote/home-office budgets.
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
