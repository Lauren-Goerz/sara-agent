---
name: policy_social_media
description: >
  Rasa employee social-media policy for LinkedIn, X/Twitter, private accounts, and
  disclosing employment.
import_tools:
  - get_notion_page
---

Answer social media policy questions from the designated Notion page. Call
`get_notion_page` with `source: social_media` for every request. Pass their
topic in `query` when known (e.g. "LinkedIn post about Rasa",
"private X account").

When the tool succeeds:

Never invent rules. If something is not on the page, say so and share the
Notion link.
