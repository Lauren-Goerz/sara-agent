---
name: leave_balance
description: >
  Live BambooHR leave balances or requests: remaining PTO, vacation, or sick
  days and "request time off for me". Not booking guidance, entitlement,
  carry-over, sick-leave steps, parental leave, or benefits.
---

Sara does not have live BambooHR API access yet, so do not invent balances,
request ids, or demo roster answers.

For live time-off balances, who's out, or submitting a leave request in
Bamboo, point them here:

- Open BambooHR: <https://rasa.bamboohr.com/home/|rasa.bamboohr.com>
- Or open the *BambooHR* app under Apps in Slack (DM the BambooHR bot) and
  ask in natural language, e.g. "How much time off do I have?" / use
  `/requesttimeoff` if they prefer.
- Remind them Bamboo's natural-language answers work in the BambooHR app
  conversation, not in other channels.

To submit a request in Bamboo they can also use `/requesttimeoff` in the
BambooHR Slack app.

If they ask how to plan vacation, offline days, or OOO steps, that is
@skill.leave_vacation - not this one.

If they ask how many vacation days they get, carry-over rules, or country
vacation policy, that is @skill.policy_vacation.

If they ask what to do because they are sick (steps, certificates, country
rules), that is @skill.leave_sick.

If they ask about parental, maternity, paternity, or adoption leave, that is
@skill.leave_parental.

Keep the reply short and friendly.

If they ask for a colleague's balance, say you can't look that up and they
(or People Ops) should use BambooHR directly.
