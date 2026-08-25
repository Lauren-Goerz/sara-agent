---
name: lookup_kandji
description: >
  Kandji/Iru FAQ: what it is, Mac MDM/device management, keystroke concerns,
  monitoring, and who has access. Not CrowdStrike, live incidents, or
  security/compliance policy.
---

Answer Kandji / Iru questions from the designated Notion page. Call
`get_kandji_info` for every request - pass their topic in `query` when
known (e.g. "what is it", "keystrokes", "who has access").

On follow-ups, call the tool again with the new `query`.

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.- Always finish with:
  <https://app.notion.com/p/rasa/Kandji-Iru-1f4b9c0d544a8029888cd852181b9b58|Kandji / Iru>

Never invent what Kandji/Iru monitors or who can access it. If something is
not on the page, say so and share the Notion link (and #security if useful).
If the page is unavailable, share the same link and do not guess.
