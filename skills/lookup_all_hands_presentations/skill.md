---
name: lookup_all_hands_presentations
description: >
  All Hands, townhall, or offsite slides and recordings from January 2025
  onward. Activate for "All Hands slides", "All Hands recording", "most
  recent All Hands deck", "last All Hands", "latest All Hands", "offsite
  slides", "townhall recording", or "where are the All Hands
  presentations?". Not the sales pitch deck (sales_asset_pitch_deck).
---

Call `get_all_hands_event` once with the user's wording in `query`.

Pass their message through as-is, including follow-ups like "the one before
that", "earlier", or "the next one" — the tool tracks which event it last
posted and steps from there. Never rewrite a relative follow-up into a
specific date yourself.

The tool posts the Slack answer itself. After it returns, do not send
another message and do not invent a deck, recording, or Notion URL.
