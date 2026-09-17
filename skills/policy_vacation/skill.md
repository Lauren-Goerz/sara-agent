---
name: policy_vacation
description: >
  Vacation/PTO entitlement by country, carry-over, holiday half-days, offline-day
  allowance (including overtime make-up), and sickness during vacation.
---

Answer vacation **policy** (entitlements and country rules), not how to book.

Call `get_vacation_policy_guidance` with their `question` and any country they
named as `location_override`.

Use only the tool fields. Never invent statutory days, carry-over caps, or
country rules:

- Entitlement: quote only their geography from `entitlement_content` and use
  `entitlement_slack_link`.
- Carry-over, half-days, offline allowance, or sickness during vacation: use
  only that item from `shared_sections`. If `shared_sections.carry_over` is
  present, quote it — never say the page has no carry-over rule. For offline
  days, always say they must confirm with their Manager first before booking.
- `local_section` is extra context, never a substitute for entitlement.
- If `ask_for_location`, the picker was sent; send nothing else. Call again
  with `location_override` after their reply.
- If `entitlement_ok` is false, link the Benefits page and do not guess.

Do not treat sick-certificate country blocks as vacation policy.

Keep replies short. For live remaining balances, that is @skill.leave_balance.
For how to book in Bamboo / OOO steps, that is @skill.leave_vacation.
