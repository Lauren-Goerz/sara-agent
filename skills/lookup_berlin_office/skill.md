---
name: lookup_berlin_office
description: >
  Working from the Berlin office - desks, access, office norms, and
  day-to-day HQ guidance. Activate for "Berlin office", "working from the
  Berlin office", "office access Berlin", "desk in Berlin HQ", or similar.
  Do NOT activate for relocating to Berlin/Germany (lookup_relocation_germany).
  Do NOT activate for remote / home office budget (lookup_remote_budget).
  Do NOT activate for temporary work abroad (policy_work_abroad). Do NOT
  activate for generic Notion search when this page clearly applies.
---

Answer Berlin-office questions from the designated Notion page. Call
`get_berlin_office` for every request - pass their topic in `query` when
known (e.g. "access", "desk", "wifi", "visitors").

On follow-ups, call the tool again with the new `query`.

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.- Always finish with:
  <https://app.notion.com/p/rasa/Working-from-Berlin-Office-7a57e119a0fb443b9c9ce6a481e14578|Working from Berlin Office>

Never invent access rules, desk policies, or office details. If something is
not on the page, say so and share the Notion link. If the page is
unavailable, share the same link and do not guess.
