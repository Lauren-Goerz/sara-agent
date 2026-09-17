---
name: security_incidents
description: >
  Check whether Rasa was affected by a named vulnerability, CVE, vendor incident, RCE, or
  supply-chain compromise.
import_tools:
  - get_notion_page
---

Answer security-incident / "were we affected?" questions from the designated
Notion tracker. Call `get_notion_page` with `source: security_incidents` for
every request. Pass the incident/CVE/vendor in `query` when known.

When the tool succeeds:
- Answer only from `source_content`.
- For a named incident (Trivy, supply chain, RCE, CVE…): say whether it is
  listed and what the tracker says about Rasa impact. If it is not listed,
  say so plainly - do not invent an all-clear or a breach.
- For broad "any incidents?" asks: give a short factual summary from the
  tracker, or point people to the page if it is long.

Never invent incidents, impact, timelines, or customer exposure.
