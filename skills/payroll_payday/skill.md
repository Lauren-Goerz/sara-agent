---
name: payroll_payday
description: >
  How many days until payday / next salary payment at Rasa. Activate for
  "when is payday", "how many days until payday", "when do we get paid",
  "next pay date", or similar. Uses employment location: Germany/Serbia/
  France/UK around the 26th; US twice a month; Deel twice a month or last
  day of month. Do NOT activate for leave balances (leave_balance), public
  holiday calendars (lookup_public_holidays), benefits (benefits), or
  payslips / paychecks (payroll_payslip).
---

Answer "how many days until payday?" with `get_days_until_payday`.

1. Call the tool (it reads Slack location/timezone when possible).
2. If it asks for location, the tool already sent a country picker; do not
   repeat the question. If it asks for the Deel schedule, ask one short
   clarifying question. Then call again with `location_override` or
   `pay_setup` (`deel_semimonthly` or `deel_month_end`).
3. When it succeeds, reply with `days_phrase` until `next_payday_estimate`,
   plus a brief note from `rule_summary`. Say it is an estimate because
   weekends/public holidays can shift the exact day.

Rasa rules to remember (also enforced in the tool):
- Germany, Serbia, France, UK: around the 26th
- US: twice a month (mid-month and month-end)
- Deel: twice a month OR last day of the month

Never invent a different payroll calendar. Keep it short and Slack-friendly.
