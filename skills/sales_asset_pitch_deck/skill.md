---
name: sales_asset_pitch_deck
description: >
  Find Rasa's standard pitch deck, talk tracks, DIY deck, and pitch support materials. Not
  All Hands decks.
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

Do not invent a Google Slides URL.
