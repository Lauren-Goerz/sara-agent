---
name: lookup_employee_handbooks
description: >
  Official Rasa employee handbooks by country. Activate for "employee
  handbook", "staff handbook", "handbook for Germany/US/UK/…", "is there a
  handbook for my country", or similar. Do NOT activate for a specific
  named policy (travel, benefits, whistleblower, sexual harassment,
  anti-bribery, etc.) - use that dedicated skill. Do NOT activate for
  generic Notion search when the ask is clearly for a country handbook.
  Do NOT activate for People / HR helpdesk ticket intake - that is
  helpdesk_intake.
---

Help people find the official employee handbook for their country.

Call `get_employee_handbooks` for every request - pass their country or
topic in `query` when known (e.g. "Germany", "US", "Ireland").

On follow-ups, call the tool again with the new `query`.

When the tool succeeds:
- Answer from `source_content` only.
- Official handbooks exist **only** for the countries listed on that page.
  Share the matching country link(s) from the page when present.
- If they ask for a country that is **not** listed, say clearly that Rasa
  does not publish an official employee handbook for that country. Offer to
  help with general Rasa policy questions instead (benefits, leave, travel,
  etc.) and invite them to ask.
- Keep it short and Slack-friendly.
- Always finish with:
  <https://app.notion.com/p/rasa/Employee-Handbooks-defd5187553d4e8598e412a115679b40|Employee Handbooks>

Never invent a handbook, country, or file link that is not on the page. If
the page is unavailable, share the same Notion link and do not guess which
countries have handbooks.
