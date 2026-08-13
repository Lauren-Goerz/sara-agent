---
name: lookup_holidays
description: >
  Public / bank holiday lookup worldwide - "is it a holiday in Bayern
  today?", "is tomorrow a holiday in Germany?", "holidays in Denmark this
  month", "is Christmas a public holiday in Japan?", US/UK/DE state or
  country holiday checks. Activate for holiday / public holiday / bank
  holiday questions about a place and date. Do NOT activate for Rasa
  company holiday / office closure policies unless they clearly want the
  public-holiday calendar. Do NOT activate for leave booking (leave_vacation)
  or work-abroad policy (policy_work_abroad).
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
