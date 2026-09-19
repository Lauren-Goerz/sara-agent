---
name: leave_sick
description: >
  What to do when you yourself are sick: Bamboo booking, doctor's notes, surgery
  leave, and country-specific sick rules. Not caring for a sick child or relative
  (leave_dependent_care), vacation, or parental leave.
import_tools:
  - get_vacation_sick_guidance
---

Call `get_vacation_sick_guidance` with `topic: sick`. Use only its returned
sections.

Reply with `everyone_section`, then `local_section` only if present, and
`surgery_section` only when relevant. They book a sick day in Bamboo from day
one even if they worked a few hours. Include `bamboo_slack_link` when booking
is mentioned.

If `required_preface` is present, begin with that exact sentence before the
local rules. If `ask_for_location` is true, a country picker was already sent;
on their reply call again with `location_override`.

- Every reply ends with the source_slack_link string from the tool result, pasted exactly. Never name the page without it and never tell anyone to search for it in Notion.
