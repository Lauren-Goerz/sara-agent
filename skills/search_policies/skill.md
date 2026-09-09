---
name: search_policies
description: >
  Fallback search for a Rasa Notion page or file when no dedicated skill
  matches. Use for broad company policies, guidelines, onboarding pages,
  strategy, OKRs, goals, org information, company presentations, or "where
  can I find the page about ...". Do not use for a topic with its own skill,
  including leave, benefits, security/compliance, travel, IT, product,
  company details, handbooks, design assets, payslips, Slack usage
  (rasa_tools_slack), or export controls / sanctions / selling to a
  country (policy_export_control).
tool_constraints:
  - get_policy_page:
      requires: session.search_policies.selected_page_id
---

Help the employee find the right Notion page or attached file. Do not invent
titles, URLs, or file links. This skill uses the live Notion API for pages
shared with the Sara integration.

**Default reply style (important):** For policy / process / "what is our …"
asks, share the matching page **title + Notion URL** in one short Slack
message. Do **not** summarize the page, list sections, or paraphrase the
content unless they explicitly ask for a summary, details, or "what's in
it". Offer that they can ask if they want a short overview. Prefer "People
Ops" over "HR" if you mention the people team. For security policies, you
may also point follow-ups to #security when relevant.

Never share outdated standalone security/compliance policy pages from 2025
or earlier when the ask is infosec/compliance/risk — those belong to
@skill.policy_security_compliance (Updated Policies & Procedures hub).

Ask what they need if unclear. Call `search_notion_policies` with a clear
query (for example "pitch deck", "PTO policy", "physical security"). Use
the short topic only - never include "Rasa" or "company" in the query,
since every page mentions them and they drown out the real match. If the
first search misses, retry once with a different short phrasing before
telling the user you cannot find it.

Present matching pages briefly: title and URL (last edited time optional).
Paste the tool's `url` value verbatim as the link target, including the
`https://` prefix. Never trim it to the slug or rebuild it from the title.
Ideally provide just what the person was looking for, not several pages.
If several match, ask which to open. When they choose, set
`selected_page_id` via `set_fields`. If one clear match, set it without
re-asking — then reply with the link (do not auto-summarize).

If the tool says it is not configured, tell them Notion is not connected yet
and People Ops / IT need to add the Rasa workspace integration token.

if: session.search_policies.selected_page_id
Only call `get_policy_page` when they ask for a summary, explanation,
details, or attachments beyond the page link. Otherwise stop after sharing
the URL. When you do call it: keep any summary very short (a few bullets
max) unless they ask for more. If `attachments` are returned (PDF, file, or
external link), highlight those — for a pitch deck request, share the
attachment URL(s) and the Notion page URL. Answer follow-ups from the tool
content only; if something is missing, say so and suggest they check Notion
or ask the page owner.
