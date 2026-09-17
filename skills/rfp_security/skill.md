---
name: rfp_security
description: >
  Answer vendor RFP/RFI security questionnaires from the approved bank when no dedicated
  policy skill applies.
import_tools:
  - get_notion_page
---

Help answer vendor / RFP / RFI security questionnaire questions from the
approved bank — **only** when a dedicated policy skill does not already
cover the topic.

Call `get_notion_page` with `source: rfp_security` for every request. Pass the
topic or question in `query`.

When the tool succeeds:
- Use only `source_content` from the bank.
- Prefer matching entries to `query` and reuse approved wording.
- Keep the Slack reply short; offer a longer paste-ready draft if useful.
- Tell them to open the bank and double-check the source before using the
  answer externally.

Never invent certifications, controls, audit dates, or security claims that
are not in the bank. If nothing matches, say so and share the Notion link
(and suggest #security if needed).
