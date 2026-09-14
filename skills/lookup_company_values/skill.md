---
name: lookup_company_values
description: >
  Rasa's official company values and their descriptions.
import_tools:
  - get_notion_page
---

Answer questions about Rasa's official company values from the designated live
Notion page. Call `get_notion_page` with `source: company_values` for every
request. Do not answer from memory or invent values.

When the tool succeeds:
- List each value by its exact name from `source_content`.
- Include the short description under each value.
- Keep behavioral examples brief or omit them unless the user asks for detail.

Never invent, rename, or reorder values. Answer follow-ups from the tool
content only.
