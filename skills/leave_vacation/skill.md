---
name: leave_vacation
description: >
  How to book vacation or offline days, set OOO messages, or what to do after
  working overtime or on a public holiday (offline day). Not balances,
  entitlement, or carry-over.
---

Call `get_leave_booking_guidance` with the matching topic:

- `topic: offline` — overtime, worked on a public holiday, offline days, or
  how to take time back for extra hours
- `topic: vacation` — booking vacation / PTO in Bamboo
- `topic: ooo` — the OOO email template

Answer only from `section_text`.

When `must_confirm_with_manager` is true (offline / overtime), always say they
must speak with their Manager first before booking an offline day. Never skip
that step. Never invent overtime pay.

Include `bamboo_slack_link` when booking is mentioned, and always paste
`source_slack_link`.

For balances use @skill.leave_balance. For entitlement, carry-over, holiday
half-days, or how many offline days are allowed per year use
@skill.policy_vacation.
