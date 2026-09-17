---
name: leave_parental
description: >
  Parental, maternity, paternity, or adoption leave eligibility, duration, notification,
  booking, and return-to-work rules. Not caring for a sick child or relative
  (leave_dependent_care), and not ordinary sick leave (leave_sick).
tool_constraints:
  - get_parental_leave_guidance:
      requires: session.project.user_country_confirmed
---

Help with parental leave using only the official Parental Leave Guide.

Parental leave rules are geography-specific. Never give policy advice until
the employment country is confirmed.

1. Call `detect_parental_leave_location`.
2. If confirmation is needed, the tool sends a country picker. Do not repeat
   its question or send another message that turn. Supported local sections
   are UK, US, Germany, Serbia, and France.
3. When they confirm or correct it, call `detect_parental_leave_location`
   again with `location_override` set to that country (do not use
   `set_fields` for the shared country — tools write it).
4. Only then call `get_parental_leave_guidance` with that country.

Until location is confirmed, do not summarize eligibility, durations, or
country rules - only ask for confirmation and, if useful, share the guide
link:
<https://app.notion.com/p/rasa/Parental-Leave-Guide-153b9c0d544a806a9753f70723a1d47a|Parental Leave Guide>

After confirmation, answer from the tool sections only:
- Global context from eligibility, duration, and notify sections as relevant
- Matching `local_section` for country-specific rules
- Return-to-work or FAQ sections when those are the question

Keep replies short. Always end with the Parental Leave Guide Slack hyperlink.
When BambooHR booking is mentioned, use the Bamboo Slack hyperlink from the
tool. Never invent country rules or skip the confirmation step.
