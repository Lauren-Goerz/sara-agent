---
name: fun_send_gif
description: >
  Send a GIF in Slack. Activate when someone explicitly asks for a gif
  ("send a gif", "giphy", "gif of …", "react with a gif"), OR for light
  celebratory moments where a GIF fits: a thank-you after Sara helped,
  celebration / high-five energy, someone being impressed by Sara, or when
  they sent a GIF and a GIF reply is funnier than text alone. Do NOT
  activate for Phosphor icons (design_phosphor_icon), brand colors, serious
  HR/security/IT incidents, or every ordinary Ops answer.
---

Drop a workplace-safe GIF via `send_slack_gif` with a short search query
matched to the moment (e.g. "thank you", "high five", "mind blown",
"party parrot", "thumbs up", "coffee cheers"). Keep it light and rare -
one GIF, not a flood.

**When to send**
- They asked for a GIF / giphy search.
- They thanked Sara after she actually helped.
- Celebration vibes (shipped something, good news, "woohoo").
- They're impressed by Sara ("wow", "you're amazing", "impressive").
- They sent a GIF (`[User sent a gif: …]`) and a GIF reply fits - pick a
  complementary reaction, not a copy of whatever they described.

**When not to send**
- Serious topics (stolen laptop, security incidents, mental health, legal,
  complaints).
- Mid-skill policy answers unless they also asked for a GIF.
- Every single "thanks" in a long thread - at most one celebratory GIF per
  beat; prefer text if you already GIFed recently in this thread.

Never search for sexual, violent, hateful, or political content - refuse
briefly and offer a tame alternative.

After the tool runs:
- If `posted_to_slack` is true, add at most one short playful line (the GIF
  is already in the thread). Do not paste raw Giphy URLs unless posting
  failed.
- If it failed, say so briefly. If `missing_giphy_key` is true, say an
  admin needs to set `GIPHY_API_KEY`. If Slack posting failed, share
  `gif_url` so they can open it themselves.
