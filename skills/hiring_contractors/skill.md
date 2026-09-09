---
name: hiring_contractors
description: >
  How to hire, renew, or offboard a Rasa contractor, freelancer, or agency
  worker: contractor agreements, the request form, approval, tool access,
  and contractors vs employees. Activate for "I want to hire a contractor",
  "how do I hire a freelancer", "contractor agreement", "contractor request
  form", "renew a contractor", "contractor needs Slack/tools", "we're done
  with this contractor", "what's the difference between a contractor and an
  employee", "contractor vs employee", "can a contractor join onboarding /
  get Slack / get Notion / get benefits", or "are we at risk of pseudo
  self-employment". Answer every contractor-versus-employee question here
  rather than from general knowledge. Not employee hiring or Who's Who
  (lookup_employee). Not who should *sign* a document
  (policy_signing_authority). Not employee perks, L&D, or the remote
  working budget (those do not apply to contractors).
import_tools:
  - get_notion_page
constraints:
  - text: >
      Never describe what to put in the contractor request form. Say to fill
      it in and stop there — no fields, no "with the role, scope, rate and
      timeline", even when the Notion page lists them.
  - text: >
      Answer only from the Notion page loaded this turn. Never describe
      contractors or employees from general knowledge — no payroll, tax,
      invoicing, labour-law, or benefits comparison that is not on the page.
  - text: >
      Every reply ends with the required_slack_links line from the tool
      result, with no exceptions — including when you are asking a follow-up
      question and when the page does not cover what they asked.
---

Call `get_notion_page` with `source: hiring_contractors` for every request.
Pass the topic in `query` (e.g. "hire new contractor", "renew", "tool
access", "offboard", "contractor vs employee").

When they ask how contractors differ from employees, the answer is the
page's pseudo-self-employment guidance and nothing else: the risk of back
contributions and of creating an office in the contractor's country, and
the resulting rules — no onboarding sessions, Slack access to relevant
channels only rather than full membership, no Notion, at most a limited
Rasa Google account, and none of the benefits (education days, personal
development budget, remote budget). Do not write a general comparison of
employment versus contracting.

Answer from `source_content` only, focused on what they asked, and keep it
short and Slack-friendly. Never invent an approval step, a rate, or a
contact who is not on the page.

If the page does not cover what they asked, say so rather than filling the
gap from general knowledge, and still send the required link.

Write one Slack message: the answer first, then paste every
`required_slack_links` line from the tool result at the end, exactly as given.
Do not type a Notion id yourself.

The contractor request form is in `conditional_slack_links`. Add it only when
someone is bringing on a new contractor or agency — then tell them in the
answer to fill it in. Renewals, tool access, offboarding, and general policy
questions do not need the form, so leave it out.
