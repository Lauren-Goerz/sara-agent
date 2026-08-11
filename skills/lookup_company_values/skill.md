---
name: lookup_company_values
description: >
  Share Rasa's official company values, culture principles, and how the team
  works together. Activate when the user asks "what are Rasa's values?",
  "company values", "core values", "our values", mission/culture principles,
  or how Rasa's values are defined. Do not use the general policy search for
  these requests.
---

Answer questions about Rasa's official company values from the designated live
Notion page. Call `get_company_values` for every request - do not answer from
memory or invent values.

When the tool succeeds:
- List each value by its exact name from `source_content`.
- Include the short description under each value.
- Keep behavioral examples brief or omit them unless the user asks for detail.
- Always finish with the Notion link:
  <https://app.notion.com/p/rasa/Rasa-s-Company-Values-f3afec52e31742f292f9a776d4ef712d|Rasa's Company Values>.

Never invent, rename, or reorder values. Answer follow-ups from the tool
content only. If the page is unavailable, say so and share the same Notion
link - do not guess.
