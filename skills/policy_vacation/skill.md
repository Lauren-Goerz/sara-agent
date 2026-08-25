---
name: policy_vacation
description: >
  Country vacation/PTO policy: entitlement, days granted, carry-over,
  holiday half-days, offline-day allowance, and sickness during vacation.
  Not live Bamboo balances or booking/OOO steps.
---

Answer vacation **policy** (entitlements and country rules), not how to book.

Always call `get_vacation_policy_guidance` first. Pass `location_override`
when they named a country. Pass `question` with their ask (carry-over, half
days, allowance, offline allowance, sick during vacation).

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

1. Shared company rules from `shared_sections` when they match the question.
2. Country rules only from `local_section` / `handbook_section`.
3. If `ask_for_location` is true and they need local rules, ask which country
   they work in, then call again with `location_override`.
4. India and other geographies with no local section: do not quote Germany,
   UK, Serbia, France, or US rules.

Do not treat sick-certificate country blocks as vacation policy.

Keep replies short. Always include `source_slack_link`. For live balances,
that is @skill.leave_check. For how to book in Bamboo / OOO steps, that is
@skill.leave_vacation.
