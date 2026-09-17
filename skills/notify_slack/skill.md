---
name: notify_slack
description: >
  Post or announce a user-provided message to an allowed Slack channel after confirmation.
tool_constraints:
  - post_slack_message:
      requires: >
        session.notify_slack.channel_id
        and session.notify_slack.message_text
      requires_confirmation:
        enabled: true
        utter_for_confirmation: utter_ask_post_confirmation
        utter_on_user_denial: utter_post_cancelled
---

Help the employee post a short message to a public Slack channel. Do not invent
delivery receipts. This skill posts for real via the Slack API.

Clarify which channel and what to say if either is missing. Call
`list_slack_channels` when they are unsure of channel names. Draft the message
and show them the exact text plus channel.

Never post confidential employee data, compensation, medical details, or
performance notes to Slack - refuse and suggest People Ops instead.

When the draft is ready, set `channel_id` (prefer the id from
`list_slack_channels`) and `message_text` via `set_fields`, then call
`post_slack_message`. The engine will ask them to confirm before the post
runs. Share the returned permalink. If the tool says it is not configured,
tell them the Slack bot token is missing from the environment.
