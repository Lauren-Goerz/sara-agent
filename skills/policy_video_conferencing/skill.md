---
name: policy_video_conferencing
description: >
  Video conferencing at Rasa - Google Meet, Zoom, Zoom license requests,
  which tool to use for calls/meetings, or "how do we do video calls".
  Activate for "Google Meet", "Zoom license", "video conferencing", "which
  meeting tool", or similar. Not the Berlin office meeting-room TV / Zoom
  Room (office_berlin). Do NOT activate for Slack huddles as a
  general chat question, or for product docs about Rasa voice channels.
---

Answer video-conferencing questions briefly and Slack-friendly.

**Default.** Rasa uses **Google Meet** for video conferencing. Prefer Meet
for internal and external calls unless they have a specific Zoom need.

**Zoom licenses.** If someone needs Zoom (or another paid video tool), tell
them to open a Wrangle ticket to request software:
1. Type `/wrangle` in any Slack channel.
2. Create a ticket requesting the Zoom license / software.
3. Include why they need it (customer requirement, event, etc.) when known.

**Hard rules.**
- Do not invent license costs, approval owners, or turnaround times.
- Do not create the Wrangle ticket yourself.
- Do not claim Rasa "doesn't use Zoom at all" - Meet is the default; Zoom
  is available via a software request when needed.
