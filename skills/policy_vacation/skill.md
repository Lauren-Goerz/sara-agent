---
name: policy_vacation
description: >
  How many vacation/PTO days someone is entitled to by country, plus
  carry-over, holiday half-days, offline-day allowance, and sickness during
  vacation. Activate for "how many vacation days do I get", "annual leave
  allowance", or country PTO entitlement. Not live Bamboo balances or
  booking/OOO steps.
---

Answer vacation **policy** (entitlements and country rules), not how to book.

Always call `get_vacation_policy_guidance` first. Pass `location_override`
when they named a country. Pass `question` with their ask (how many days,
carry-over, half days, offline allowance, sick during vacation).

The tool resolves the country once and shares it with the other country-aware
skills: what they said this turn, then the country already established in this
conversation, then Slack *My Location*, then timezone. Whenever
`required_preface` is present, begin the personalized part with this exact
sentence:

"based on the location information you provided in your Slack profile..."

Do not use that preface when they explicitly supplied or corrected their
country.

Use only the tool fields. Never invent statutory days, carry-over caps, or
country rules:

1. For "how many vacation days / entitlement / allowance": use only
   `entitlement_content` from Benefits & Perks 2026. Quote the number for
   their geography. Always finish with `entitlement_slack_link`.
2. Shared company rules (carry-over, half days, offline days, sick during
   vacation) from `shared_sections` - quote only the rule they asked about,
   never the full set.
3. Extra country handbook text only from `local_section` / `handbook_section`
   when present — never as a substitute for the Benefits day count.
4. If `ask_for_location` is true, the tool already sent a country picker.
   Do not repeat the country question or send another message that turn.
   When they select or type a country, call again with `location_override`.
5. If `entitlement_ok` is false, share `entitlement_slack_link` and say the
   day count is on that page. Do not guess.

Do not treat sick-certificate country blocks as vacation policy.

Keep replies short. For live remaining balances, that is @skill.leave_balance.
For how to book in Bamboo / OOO steps, that is @skill.leave_vacation.
