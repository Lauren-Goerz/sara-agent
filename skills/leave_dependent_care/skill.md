---
name: leave_dependent_care
description: >
  Time off to care for a sick child or another relative such as a parent,
  partner, or sibling. Activate for "my kid is sick", "my mum is in hospital",
  or "do I book a sick day for this". Not your own illness (leave_sick), not
  vacation, and not parental leave.
import_tools:
  - get_vacation_sick_guidance
---

Call `get_vacation_sick_guidance` with `topic: dependent_child` or
`topic: dependent_family`.

For a sick child, use only `child_sick_section`: still working some hours means
book nothing; book a normal sick day only when taking the day off. Never invent
a "sick child" leave type.

For any other relative, use only `family_care_section`. Mention
`offline_section` only if they ask about the offline-day allowance. Never say
the whole absence is sick leave or that vacation is required.

Include `bamboo_slack_link` when booking is mentioned.

- Every reply ends with the source_slack_link string from the tool result, pasted exactly. Never name the page without it and never tell anyone to search for it in Notion.
