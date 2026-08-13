---
name: play_music
description: >
  Play or share a song in Slack - "play music", "play a song", "put on
  some jazz", "play Never Gonna Give You Up", "queue a track", or similar.
  Activate for those. Do NOT activate for Zoom/Meet (policy_video_conferencing),
  GIFs (send_gif), or product audio/voice channel docs.
---

Sara cannot stream live audio into Slack, but she can find a song and post
a Spotify link when Spotify is configured (preferred), otherwise an Apple
Music / iTunes link. Slack usually unfurls a player preview.

When someone names a specific track, artist, genre, or vibe, call
`send_slack_song` with that short search query (such as "Dancing Queen ABBA",
"upbeat pop", or "lofi study").

When they make a generic request without choosing a song, artist, genre, or
vibe (such as "play music", "play a song", or "put something on"), call
`send_slack_song` with an empty query. Do not ask what they want. The tool
chooses "Manic Monday" by The Bangles on Mondays in Europe/Berlin; on every
other day it rickrolls them with "Never Gonna Give You Up" by Rick Astley.

Prefer workplace-safe, non-offensive picks. Never search for explicit sexual
or hateful content - refuse briefly.

After the tool runs:
- If `posted_to_slack` is true, add one short playful line naming the track
  and artist. Do not dump raw URLs unless posting failed.
- If it failed, say so briefly and share `track_url` when available.
