---
name: lookup_security_incidents
description: >
  Rasa security incidents and vulnerability impact questions - "has Rasa had
  any security incidents", "was Rasa affected by the Trivy supply chain
  compromise", remote code execution / CVE / supply-chain impact on Rasa,
  or similar security-status asks. Activate for those. Do NOT activate for
  product how-tos (redirect_product_docs), competitive analysis, RFP/RFI
  security questionnaire drafting (rfp_security), or general Notion policy
  search when the ask is clearly security-incident status.
---

Answer security-incident / "were we affected?" questions from the designated
Notion tracker. Call `get_security_incident_status` for every request - pass
the incident/CVE/vendor in `query` when known.

When the tool succeeds:
- Answer only from `source_content`.
- For a named incident (Trivy, supply chain, RCE, CVE…): say whether it is
  listed and what the tracker says about Rasa impact. If it is not listed,
  say so plainly - do not invent an all-clear or a breach.
- For broad "any incidents?" asks: give a short factual summary from the
  tracker, or point people to the page if it is long.
- Always finish with:
  <https://app.notion.com/p/rasa/202b9c0d544a8143be59e3e3568b1b4d?v=202b9c0d544a816bb595000c37f7dab3|Security incidents tracker>

Never invent incidents, impact, timelines, or customer exposure. If the page
is unavailable, share the same link and do not guess.
