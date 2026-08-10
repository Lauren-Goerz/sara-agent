---
name: search_policies
description: >
  Search Rasa's Notion for company docs — policies, handbook, pitch decks,
  sales decks, onboarding pages, and similar. Activate when the user asks
  about a policy, handbook, guidelines, "what's our policy on…", "latest
  pitch deck", sales deck, company presentation, or where to find a Notion
  page/file.
tool_constraints:
  - get_policy_page:
      requires: session.search_policies.selected_page_id
---

Help the employee find the right Notion page or attached file. Do not invent
titles, URLs, or file links. This skill uses the live Notion API for pages
shared with the Sara integration.

Ask what they need if unclear. Call `search_notion_policies` with a clear
query (for example "pitch deck", "PTO policy", "remote work"). Present
matching pages briefly: title, last edited time, and URL.

If they ask for the "latest" of something (e.g. latest pitch deck), prefer
the most recently edited match from the tool results.

If several match, ask which to open. When they choose, set `selected_page_id`
via `set_fields`. If one clear match, set it without re-asking.

If the tool says it is not configured, tell them Notion is not connected yet
and People Ops / IT need to add the Rasa workspace integration token.

if: session.search_policies.selected_page_id
Call `get_policy_page`. Summarize the page body in plain language. If
`attachments` are returned (PDF, file, or external link), highlight those
first — for a pitch deck request, share the attachment URL(s) and the
Notion page URL. Answer follow-ups from the tool content only; if something
is missing, say so and suggest they check Notion or ask the page owner.
