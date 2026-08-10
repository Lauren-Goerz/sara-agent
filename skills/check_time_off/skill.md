---
name: check_time_off
description: >
  Check PTO / vacation / sick leave balances or draft a time-off request
  (BambooHR). Activate when the user asks about time off, PTO balance,
  vacation days left, sick leave, or wants to request time off.
tool_constraints:
  - get_time_off_balance:
      requires: session.check_time_off.selected_employee_id
  - submit_time_off_request:
      requires: session.check_time_off.request_confirmed
---

Help the employee with BambooHR time off. Do not invent balances, types, or
request ids.

Identify who the balances are for. If they say "my" or do not name anyone,
ask for their name (demo roster) and call `resolve_employee` with that name.
When they name someone, call `resolve_employee`. If several match, ask which
one, then set `selected_employee_id` via `set_fields`. If one clear match,
set `selected_employee_id` to that id.

if: session.check_time_off.selected_employee_id
Call `get_time_off_balance` and present each type with remaining units.
If they only wanted a balance check, stop there unless they ask for more.

If they want to request time off, gather start date, end date, and type
(Vacation, Sick, or Personal). Call `list_time_off_types` if they are unsure
of the type name. Summarize the request and ask them to confirm. When they
confirm, set `request_confirmed` to true via `set_fields`, then call
`submit_time_off_request` with the dates and type. Share the returned
request id. Remind them this is a demo submission until live BambooHR is wired.
