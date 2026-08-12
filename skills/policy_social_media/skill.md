---
name: policy_social_media
description: >
  Rasa social media policy - posting about Rasa on LinkedIn, private
  X/Twitter accounts, personal vs work social posts, disclosing employment,
  and related employee social media rules. Activate for "can I post about
  Rasa on LinkedIn", "can I have a private Twitter/X account", "social media
  policy", or similar. Do NOT activate for marketing campaign strategy or
  competitive analysis. Do NOT activate for general Notion search when this
  policy clearly applies.
---

Answer social media policy questions from the designated Notion page. Call
`get_social_media_policy` for every request - pass their topic in `query`
when known (e.g. "LinkedIn post about Rasa", "private X account").

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.
- Always finish with:
  <https://app.notion.com/p/rasa/Social-Media-Policy-39d0d3053dc44c9e89c2baba3230eb4c|Social Media Policy>

Never invent rules. If something is not on the page, say so and share the
Notion link. If the page is unavailable, share the same link and do not
guess.
