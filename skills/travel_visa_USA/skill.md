---
name: travel_visa_USA
description: >
  How to get a US visa for Rasa travel: B1/B2 business or tourism visa,
  application steps, DS-160, interview, ESTA vs visa, and who to ask.
  Activate for "how do I get a visa for the US", "US visa", "B1 visa",
  "B2 visa", "American visa", or similar. Not travel booking, travel
  insurance, work-abroad policy, or visas for other countries. Not 
  required for US citizens. 
import_tools:
  - get_notion_page
---

Answer US visa questions from the designated Notion page. Call
`get_notion_page` with `source: us_visa` for every request. Pass their topic
in `query` when known (e.g. "B1 business visa steps", "ESTA", "interview").

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.
- Use exact steps, forms, and contacts from the page - never invent visa
  types, processing times, or eligibility.
- Always finish with this Slack hyperlink, using the full https URL:
  <https://app.notion.com/p/rasa/US-Visa-Process-B1-B2-Tourism-Business-1f8b9c0d544a80df8ea6e5d7021653ac|US Visa Process (B1/B2)>

Never invent application steps or legal advice. If something is not on
the page, say so and share the Notion link. If they need travel booking
or spend rules, that is @skill.policy_business_travel. If they need trip
cover, that is @skill.policy_travel_insurance.
