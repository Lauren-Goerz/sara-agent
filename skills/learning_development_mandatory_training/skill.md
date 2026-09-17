---
name: learning_development_mandatory_training
description: >
  Mandatory 2026 compliance training and EasyLlama: required courses, audience, deadlines,
  and frequency.
import_tools:
  - get_notion_page
---

Answer mandatory-training questions from the designated Notion page. Call
`get_notion_page` with `source: mandatory_training` for every request. Pass
their topic in `query` when known (e.g. "who must complete", "EasyLlama",
"GDPR", "harassment", "frequency").


When the tool succeeds:
- Use the page's eligible groups, provider, frequency, and owners — never
  invent a deadline, a course, or a contact who is not on the page.

If something is not on the page, say so and share the Notion link. Further
questions go to the contacts named on the page.
