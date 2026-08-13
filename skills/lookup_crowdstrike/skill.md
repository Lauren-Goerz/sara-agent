---
name: lookup_crowdstrike
description: >
  CrowdStrike at Rasa - what it is, whether it tracks web browsing, who has
  access, Falcon/EDR endpoint security questions. Activate for "what is
  CrowdStrike", "is CrowdStrike tracking my browsing", "who has access to
  CrowdStrike", or similar. Do NOT activate for live security incidents /
  "was Rasa affected" (lookup_security_incidents). Do NOT activate for the
  security/compliance policies hub (policy_security_compliance). Do NOT
  activate for Kandji / Iru (lookup_kandji). Do NOT activate for generic
  Notion search when this page clearly applies.
---

Answer CrowdStrike questions from the designated Notion page. Call
`get_crowdstrike_info` for every request - pass their topic in `query` when
known (e.g. "what is it", "web browsing", "who has access").

On follow-ups, call the tool again with the new `query`.

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.- Always finish with:
  <https://app.notion.com/p/rasa/Crowdstrike-7e762e4d1b4e4beb917b71f4f304d375|Crowdstrike>

Never invent what CrowdStrike monitors or who can access it. If something is
not on the page, say so and share the Notion link (and #security if useful).
If the page is unavailable, share the same link and do not guess.
