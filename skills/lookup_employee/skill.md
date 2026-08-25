---
name: lookup_employee
description: >
  Look up a coworker in Rasa's Who's Who directory: identity, role, team,
  location, contact, manager/reporting line, or employee fun fact. Not board
  membership, who built Sara, or company/product trivia.
tool_constraints:
  - get_employee_details:
      requires: session.lookup_employee.selected_employee_id
---

Help the employee find a coworker in Rasa's Who's Who directory on Notion.
Do not invent people, emails, titles, or reporting lines.

Ask who they are looking for if they have not said a name, team, or role.
Call `search_directory` with their query. Present matching people briefly
using the fields the tool returns.

If several people match, ask which one. When they choose, set
`selected_employee_id` via `set_fields` to that person's id from the tool
result. If exactly one clear match, set `selected_employee_id` without
re-asking.

If the tool reports the directory is not configured or not shared, say the
Who's Who page needs to be shared with the Sara-Agent Notion integration.

if: session.lookup_employee.selected_employee_id
Call `get_employee_details` and give a short profile overview:
- Name, title, department or team, and location.
- The exact answer under `Fun fact about myself:` from `profile_notes`, when present.
- A `<url|LinkedIn>` link from the `LinkedIN` field, when present.
- A `<url|Who's Who profile>` link from `notion_url`.

Keep the overview concise. Do not omit the Who's Who link when it is returned.
Answer follow-ups about that person using the tool data only.
