---
name: lookup_employee_handbooks
description: >
  Find an official Rasa employee/staff handbook for a country and say whether
  one exists. Not a specific named policy, vacation entitlement, or helpdesk
  intake.
import_tools:
  - get_notion_page
---

Help people find the official employee handbook for their country.

Call `get_notion_page` with `source: employee_handbooks` for every request.
Pass their country or topic in `query` when known (e.g. "Germany", "US",
"Ireland").

On follow-ups, call the tool again with the new `query`.

When the tool succeeds:
- Answer from `source_content` only.
- Official handbooks exist **only** for the countries listed on that page.
  Share the matching country link(s) from the page when present.
- If they ask for a country that is **not** listed, say clearly that Rasa
  does not publish an official employee handbook for that country.
- Keep it short and Slack-friendly.
- Always finish with:
  <https://app.notion.com/p/rasa/Employee-Handbooks-defd5187553d4e8598e412a115679b40|Employee Handbooks>

Never invent a handbook, country, or file link that is not on the page.
