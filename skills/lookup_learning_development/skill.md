---
name: lookup_learning_development
description: >
  Learning & Development - education days, L&D / learning budget amounts,
  recommended ways to use the budget, courses, training, conferences, and
  certifications. Activate for "education days", "learning budget", "L&D
  budget", "how much learning budget", "recommended courses", "can I use
  budget for a conference", or similar. Do NOT activate for general
  benefits/gym/wellness (lookup_benefits), remote / home office budget
  (lookup_remote_budget), or business travel spend (policy_business_travel).
  Do NOT activate for generic Notion search when this page clearly applies.
---

Answer Learning & Development questions from the designated Notion page.
Call `get_learning_development` for every request - pass their topic in
`query` when known (e.g. "education days", "budget amount", "recommended
uses", "conference").

On follow-ups, call the tool again with the new `query`.

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.
- Use exact amounts, day counts, eligibility, and recommended uses from
  the page - never invent or combine them.- Always finish with:
  <https://app.notion.com/p/rasa/Learning-Development-a744377944c1416592c0a9fdb761b2f4|Learning & Development>

Never invent budget amounts, education-day counts, or approved uses. If
something is not on the page, say so and share the Notion link. If the page
is unavailable, share the same link and do not guess.
