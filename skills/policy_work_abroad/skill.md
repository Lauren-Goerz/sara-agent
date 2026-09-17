---
name: policy_work_abroad
description: >
  Temporary work from another country or digital-nomad requests (weeks abroad
  while already employed). Not choosing Berlin/coworking/home remote-work
  style, remote budget, vacation, business travel, or permanent relocation.
import_tools:
  - get_notion_page
---

Answer questions about working from other countries using the designated
Notion page. Call `get_notion_page` with `source: work_abroad` for every
request. Pass the destination and duration in `query` when known (e.g.
"a few weeks from Denmark", "one month in South Africa").

If they ask how long they have to **choose** their remote work option/style
after joining (Berlin office vs coworking vs home only), that is
@skill.benefits_remote_budget — do not answer from this page.

When the tool succeeds:
- Answer from `source_content` only, focused on their destination/duration.
- Include any approval steps, limits, or caveats exactly as on the page.

Never invent day limits, visa/immigration rules, tax advice, or approvals.
If the answer is not on the page, say so and share the Notion link (and
People Ops if the page points there).

When the tool fails, do not narrate the failure, hedge about whether they can
go, or list what the policy "usually" covers. Point them straight to the
Notion link as the place with the rules and to their manager / People Ops.
