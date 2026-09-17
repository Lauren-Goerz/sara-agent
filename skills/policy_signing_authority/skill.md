---
name: policy_signing_authority
description: >
  Who should sign a Rasa employment, vendor, customer, NDA, or other document by
  country/entity. Not legal review.
import_tools:
  - get_notion_page
---

Answer who should sign a given document from the designated Notion page. Call
`get_notion_page` with `source: signing_documents` for every request. Pass
the country, legal entity, and document type they named in `query` (e.g.
"Serbia employment contract", "GmbH", "customer NDA").

The page is organised by **legal entity**, not by country name:
- Rasa Technologies Inc
- Rasa Technologies LLC
- Rasa Technologies GmbH & Ltd.
- Rasa Technologies SAS

If they name a country, use this mapping (the page itself names entities, not
countries):
- US / USA / Inc → Rasa Technologies Inc
- Serbia → Rasa Technologies LLC
- Germany / GmbH → Rasa Technologies GmbH & Ltd.
- UK / Ltd → Rasa Technologies GmbH & Ltd.
- France / SAS → Rasa Technologies SAS

If they name a country that is not in that list, do not guess. List the four
entities from `source_content` and ask which one the document is for.

The page also splits **process** by document type:
- Customer contracts / NDAs: review and signature path on the page
  (not the same as the HR path).
- All other documents (HR, visa, events, purchases, employment paperwork):
  the "all other documents" steps on the page.

When the tool succeeds:
- Name the signer(s) and entity exactly as written. Do not expand initials
  or invent Slack handles that are not on the page.
- For employment / HR paperwork, include the "all other documents" steps
  (manager approval, then Sarah / Rajesh get it signed) as well as which
  entity's signatories apply, once you know the entity.

Never invent a signer, title, or legal entity. If the page does not cover
that country or document, say so, share the link, and tell them to ping
@Mat (Legal) rather than guessing.

If they actually want legal review of a contract, or who Rasa's lawyer is,
that is @skill.policy_links.
