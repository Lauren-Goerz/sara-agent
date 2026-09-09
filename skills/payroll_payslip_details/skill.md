---
name: payroll_payslip_details
description: >
  Questions about what is ON a payslip or in someone's pay: gross vs net,
  why pay changed, tax, tax class, social contributions, pension, deductions,
  bonus or commission amounts, overtime, backpay, missing or wrong pay, or
  "can you explain this line". Activate for "why is my net pay lower", "what
  is this deduction", "my pay looks wrong", "how much tax did I pay". Not
  where to download a payslip (payroll_payslip), not payday dates
  (payroll_payday), not leave balances (leave_balance).
---

Anything about the *contents* of someone's pay goes to People Ops as a
ticket. Sara has no access to pay data and must never reason about it.

Reply in one short Slack message that does three things:

1. Say plainly that you can't see pay or payslip data.
2. Tell them to raise a People Ops ticket:
   - Type `/wrangle` in any Slack channel.
   - Pick the **People / HR Issues** inbox.
   - Include the pay period and what looks wrong.
3. Stop there.

**Hard rules.**
- Never explain, estimate, or guess an amount, tax rate, deduction, or
  contribution — not even "it's usually because of X".
- Never list possible reasons their pay changed.
- Never ask them to paste, screenshot, or describe payslip figures.
- Never invent a channel, email address, or payroll contact. `/wrangle` is
  the route.
- Do not create the ticket yourself.

If they actually want to know *where* to download the payslip, that is
@skill.payroll_payslip. If they are asking when they get paid, that is
@skill.payroll_payday.
