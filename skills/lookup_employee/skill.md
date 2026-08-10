---
name: lookup_employee
description: >
  Look up a coworker in the company directory (BambooHR) — name, title,
  department, location, work email, phone, or who they report to. Activate
  when the user asks who someone is, how to reach them, who manages whom,
  or org/directory questions.
tool_constraints:
  - get_employee_details:
      requires: session.lookup_employee.selected_employee_id
---

Help the employee find a coworker in the company directory. Do not invent
people, emails, titles, or reporting lines.

Ask who they are looking for if they have not said a name, team, or role.
Call `search_directory` with their query. Present matching people briefly
(name, title, department, location).

If several people match, ask which one. When they choose, set
`selected_employee_id` via `set_fields` to that person's id from the tool
result. If exactly one clear match, set `selected_employee_id` without
re-asking.

if: session.lookup_employee.selected_employee_id
Call `get_employee_details` and share the directory fields returned
(name, title, department, location, work email, work phone, supervisor).
Answer follow-ups about that person using the tool data only.
