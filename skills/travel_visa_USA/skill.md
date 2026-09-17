---
name: travel_visa_USA
description: >
  US B1/B2 visa or ESTA guidance for Rasa travel, including application steps and
  contacts. Not other countries.
import_tools:
  - get_notion_page
---

Answer US visa questions from the designated Notion page. Call
`get_notion_page` with `source: us_visa` for every request. Pass their topic
in `query` when known (e.g. "B1 business visa steps", "ESTA", "interview").

When the tool succeeds:
- Use exact steps, forms, and contacts from the page - never invent visa
  types, processing times, or eligibility.

Never invent application steps or legal advice. If something is not on
the page, say so and share the Notion link. If they need travel booking
or spend rules, that is @skill.policy_business_travel. If they need trip
cover, that is @skill.policy_travel_insurance.
