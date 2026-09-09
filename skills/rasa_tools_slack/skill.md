---
name: rasa_tools_slack
description: >
  How Rasa uses Slack: profile/display name, status, DMs vs channels, and
  the preference for open channels. Activate for "Slack guidelines", "what
  should my Slack name be", "should this be a channel or a DM", or "how do
  we use Slack". Not posting a message as Sara (notify_slack), LinkedIn or
  other social media (policy_social_media), or helpdesk intake.
import_tools:
  - get_notion_page
---

Answer Slack-usage questions from the designated Notion page. Call
`get_notion_page` with `source: slack_guidelines` for every request. Pass
their topic in `query` when known (e.g. "profile name", "open channels",
"DMs vs public channels").

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.
- Always finish with:
  <https://app.notion.com/p/rasa/Slack-Guidelines-256b9c0d544a80d1b41dd9f62949dddd|Slack Guidelines>

Never invent naming rules or channel norms. If something is not on the
page, say so and share the Notion link.

If they want Sara to post an announcement, that is @skill.notify_slack.
If they ask about LinkedIn, X, or personal social posts, that is
@skill.policy_social_media.
