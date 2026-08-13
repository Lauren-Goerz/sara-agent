---
name: lookup_pitch_deck
description: >
  Share Rasa's standard pitch deck and the Pitch Decks Notion page (talk
  tracks, DIY deck, support materials). Activate for "pitch deck", "sales
  deck", "standard pitch deck", "company pitch", "L1 deck", "talk track for
  the pitch", or "where is the pitch deck". Do NOT activate for All Hands
  decks (lookup_all_hands_presentations), product proof points
  (lookup_product_proof_points), or competitive battle cards
  (redirect_competitive_analysis).
---

Call `get_pitch_deck` for every pitch-deck request. Do not invent slide links
from memory.

When the tool succeeds, reply in one short Slack message with:
1. The standard / L1 pitch deck link from `standard_deck_url` (prefer the
   Slack link format using `standard_deck_label`).
2. The Notion page link from `source_url` — say that page also has talk
   tracks and additional support decks.

If they specifically ask for DIY / in-flight or another variant listed in
`other_decks`, share that variant's link too, still including the Notion page.

If the tool fails, share `source_url` and say the live deck link was
unavailable. Do not invent a Google Slides URL.
