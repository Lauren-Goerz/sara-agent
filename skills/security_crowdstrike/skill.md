---
name: security_crowdstrike
description: >
  CrowdStrike/Falcon FAQ: purpose, endpoint monitoring, browsing/privacy concerns, and
  access.
import_tools:
  - get_notion_page
---

Answer CrowdStrike questions from the designated Notion page. Call
`get_notion_page` with `source: crowdstrike` for every request. Pass their
topic in `query` when known (e.g. "what is it", "web browsing",
"who has access").


When the tool succeeds:
Never invent what CrowdStrike monitors or who can access it. If something is
not on the page, say so and share the Notion link (and #security if useful).
