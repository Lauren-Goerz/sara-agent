---
name: leave_sick
description: >
  What to do when sick, sick leave steps, sick certificate / doctor's note
  requirements, or country-specific sick policy (Germany, UK, Serbia, France,
  US). Activate for phrases like "I'm sick", "I am sick what should I do",
  "sick leave policy", "do I need a doctor's note", "sick certificate". Do NOT
  activate for PTO/vacation balances - that is leave_check. Do NOT activate
  for how to plan vacation, offline days, OOO templates, or carry-over - that
  is leave_vacation. Do NOT activate for parental, maternity, paternity, or
  adoption leave - that is leave_parental.
---

Help someone who is sick (or asking about sick leave) with the official steps.

Always call `get_sick_leave_guidance` first. The tool fetches the one approved
source:
<https://app.notion.com/p/rasa/Vacation-and-Sick-days-137b9c0d544a80f3aae3eaaec6a7cf0a|Vacation and Sick days>

Use only text returned by this tool. Prefer the live Notion page; if the tool
returns a fallback snapshot, still treat that as the approved source and link
it with the Slack hyperlink from `source_slack_link` (or `bamboo_slack_link`
when telling people to book in Bamboo). Never invent country rules beyond the
returned sections.

Use these tool fields for links:
- `source_slack_link` for the Notion policy page
- `bamboo_slack_link` whenever mentioning Bamboo / BambooHR booking

Reply in short form:
1. Summarize `everyone_section` (with Bamboo hyperlinked when booking is mentioned).
2. Only if `local_section` is present, add that one geography's steps.
3. Include `surgery_section` only when relevant.
4. End with `source_slack_link`.

The tool personalizes from the Slack *My Location* profile field first, then
falls back to timezone. Whenever `required_preface` is present, begin the
personalized part with this exact sentence:

"based on the location information you provided in your Slack profile..."

Do not use that preface when the user explicitly supplied or corrected their
country.

India and unsupported geographies have no `local_section`: never mention,
list, or summarize Germany, UK, Serbia, France, or US rules for them.

If `ask_for_location` is true, provide the shared section and ask which country
only if the user needs local requirements; then call again with
`location_override`.
