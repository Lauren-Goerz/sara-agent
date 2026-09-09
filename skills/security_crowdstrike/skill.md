---
name: security_crowdstrike
description: >
  CrowdStrike/Falcon FAQ: what it is, EDR/endpoint security, browsing or
  monitoring concerns, and who has access. Not Kandji/Iru (security_kandji),
  live incidents (security_incidents), or security/compliance policy.
import_tools:
  - get_notion_page
---

Answer CrowdStrike questions from the designated Notion page. Call
`get_notion_page` with `source: crowdstrike` for every request. Pass their
topic in `query` when known (e.g. "what is it", "web browsing",
"who has access").

On follow-ups, call the tool again with the new `query`.

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.- Always finish with:
  <https://app.notion.com/p/rasa/Crowdstrike-7e762e4d1b4e4beb917b71f4f304d375|Crowdstrike>

Never invent what CrowdStrike monitors or who can access it. If something is
not on the page, say so and share the Notion link (and #security if useful).
