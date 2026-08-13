---
name: policy_sexual_harassment
description: >
  Rasa Sexual Harassment Policy - what counts as sexual harassment, how to
  report, investigation, and related workplace questions. Activate for
  "sexual harassment policy", "harassment at work", "how do I report sexual
  harassment", "inappropriate behaviour policy", or similar. Do NOT activate
  for whistleblower / speak-up / anonymous misconduct reporting in general -
  that is policy_whistleblower. Do NOT activate for anti-bribery / gifts /
  hospitality - that is policy_anti_bribery. Do NOT activate for legal
  counsel / who to contact for legal - that is policy_legal_support. Do NOT
  activate for People / HR helpdesk ticket intake - that is helpdesk_intake.
  Do NOT activate for generic Notion search when this policy clearly applies.
---

Answer sexual-harassment-policy questions from the designated Notion page.
Call `get_sexual_harassment_policy` for every request - pass their topic in
`query` when known (e.g. "definition", "how to report", "investigation",
"manager responsibilities").

On follow-ups in the same conversation, call the tool again with the new
`query` so answers stay grounded in the page.

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.
- Use exact definitions, reporting paths, and process details from the page -
  never invent or combine them.
- Be careful with sensitive topics: do not pressure them to share private
  details in Slack; point them to the official reporting path on the page.
- Always finish with:
  <https://app.notion.com/p/rasa/Sexual-Harassment-Policy-bde30194f1794d77a1b8055fca871369|Sexual Harassment Policy>

Never invent reporting channels, timelines, or outcomes. If something is not
on the page, say so and share the Notion link (and whoever the page names).
If the page is unavailable, share the same link and do not guess.
