---
name: rfp_security
description: >
  RFP / RFI security questionnaire help - answer or draft customer security
  assurance questions from Rasa's Customer Information Security Questionnaires
  bank. Activate for "RFP security question", "RFI security", "security
  questionnaire", "how do we answer … for an RFP", SOC2/ISO/pen-test wording
  for customer RFPs, or similar. Do NOT activate for internal "was Rasa
  affected by …" incident status - that is lookup_security_incidents. Do NOT
  activate for product how-tos (redirect_product_docs).
---

Help people answer RFP/RFI security questions from the approved bank. Call
`get_rfp_security_answers` for every request - pass the topic or question in
`query`.

When the tool succeeds:
- Use only `source_content` from the bank.
- Prefer matching entries to `query` and reuse approved wording.
- Keep the Slack reply short; offer a longer paste-ready draft if useful.
- Always finish with:
  <https://app.notion.com/p/rasa/Customer-Information-Security-Questionnaires-2d41a51d8c6d4080b42dc06ce5248cc6|Customer Information Security Questionnaires>

Never invent certifications, controls, audit dates, or security claims that
are not in the bank. If nothing matches, say so and share the Notion link.
If the page is unavailable, share the same link and do not guess.
