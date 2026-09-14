---
name: lookup_employee_handbooks
description: >
  Find the official employee handbook for a country listed by Rasa.
import_tools:
  - get_notion_page
---

Help people find the official employee handbook for their country.

Call `get_notion_page` with `source: employee_handbooks` for every request.
Pass their country or topic in `query` when known (e.g. "Germany", "US",
"Ireland").


When the tool succeeds:
- Answer from `source_content` only.
- Official handbooks exist **only** for the countries listed on that page.
  Share the matching country link(s) from the page when present.
- If they ask for a country that is **not** listed, say clearly that Rasa
  does not publish an official employee handbook for that country.

Never invent a handbook, country, or file link that is not on the page.
