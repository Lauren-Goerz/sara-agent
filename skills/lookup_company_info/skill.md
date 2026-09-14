---
name: lookup_company_info
description: >
  Official Rasa company details: addresses, legal entities, registration, VAT, banking,
  and phone information.
import_tools:
  - get_notion_page
---

Answer requests for official company details from the designated live Notion
page. Call `get_notion_page` with `source: company_info` for every request,
passing the exact item and any office, country, or legal entity the user named
in `query`.

If the request is ambiguous because the page contains multiple offices,
countries, legal entities, bank accounts, or VAT numbers, ask which one they
need. Do not choose one silently.

When the tool succeeds:
- List the requested item first, with a short label and the exact value from
  `source_content`.
- Include the associated office, country, or legal entity when available.
- Keep the answer concise and do not list unrelated company information.

Copy sensitive identifiers exactly. Never guess, reformat, repair, or complete
an address, VAT number, IBAN, account number, BIC/SWIFT code, registration
number, or phone number. If the requested value is absent or unclear, say so
and direct the person to the Notion page.
