---
name: lookup_public_holidays
description: >
  Public or bank holidays by date, country, state, or region. Not Rasa vacation
  entitlement.
---

Answer public-holiday questions with `lookup_public_holiday`.

Pass:
- `location`: the place they named (Bayern, Bavaria, Germany, Denmark, US…)
- `when`: today / tomorrow / yesterday / YYYY-MM-DD (default today)
- `upcoming_days`: set to 30 or 60 when they ask what is coming up / this month

When the tool succeeds, answer in one short Slack message:
- Yes/no for that date in that place
- Holiday name when it is a holiday
- Brief upcoming list only if they asked for it

Clarify that these are public/bank holidays from the holiday calendar, not
Rasa office closures. If the location is unknown, ask one clarifying
question. Never invent holidays.
