---
name: notify_slack
description: >
  Post a message to a Slack channel (general, people-ops, engineering,
  announcements). Activate when the user asks to announce something, post to
  Slack, or notify a channel - not for private DMs, HR-sensitive data, or
  how to use Slack / profile names / open-channel norms (rasa_tools_slack).
tool_constraints:
  - post_slack_message:
      requires: session.notify_slack.post_confirmed
---

Help the employee post a short message to a public Slack channel. Do not invent
delivery receipts. This skill posts for real via the Slack API.

Clarify which channel and what to say if either is missing. Call
`list_slack_channels` when they are unsure of channel names. Draft the message
and show them the exact text plus channel. Ask them to confirm.

Never post confidential employee data, compensation, medical details, or
performance notes to Slack - refuse and suggest People Ops instead.

When they confirm, set `post_confirmed` to true via `set_fields`, set
`channel_id` to the chosen channel id (prefer the id from `list_slack_channels`),
set `message_text` to the final text, then call `post_slack_message`. Share the
returned permalink. If the tool says it is not configured, tell them the Slack
bot token is missing from the environment.
