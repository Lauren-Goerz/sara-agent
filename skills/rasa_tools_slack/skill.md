---
name: rasa_tools_slack
description: >
  Rasa Slack conventions: profile name, status, DMs versus open channels, and Slack
  guidelines.
import_tools:
  - get_notion_page
---

Answer Slack-usage questions from the designated Notion page. Call
`get_notion_page` with `source: slack_guidelines` for every request. Pass
their topic in `query` when known (e.g. "profile name", "open channels",
"DMs vs public channels").

When the tool succeeds:

Never invent naming rules or channel norms. If something is not on the
page, say so and share the Notion link.

If they want Sara to post an announcement, that is @skill.notify_slack.
If they ask about LinkedIn, X, or personal social posts, that is
@skill.policy_social_media.
