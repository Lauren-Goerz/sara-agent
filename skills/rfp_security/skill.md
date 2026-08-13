---
name: rfp_security
description: >
  Vendor / RFP / RFI security questionnaire help from Rasa's Vendor Security
  Questionnaire Bank - only when no dedicated policy skill answers the ask.
  Activate for "RFP security question", "RFI security", "vendor security
  questionnaire", "how do we answer … for an RFP", SOC2/ISO/pen-test wording
  for questionnaires, or similar. Do NOT activate when
  policy_security_compliance applies (Information Security, IAM, Acceptable
  Use, IR, Change Management, Threat/Vuln, Cryptography, AppSec,
  Supplier/Contractor, Information Transfer, DLP, Cloud Services, Asset
  Management, Physical Security, etc.). Do NOT activate for
  policy_security_responsibilities, policy_intellectual_property,
  policy_anti_bribery, policy_anti_slavery, or policy_whistleblower. Do NOT
  activate for "was Rasa affected by …" - that is lookup_security_incidents.
  Do NOT activate for product how-tos (redirect_product_docs).
---

Help answer vendor / RFP / RFI security questionnaire questions from the
approved bank — **only** when a dedicated policy skill does not already
cover the topic.

Call `get_rfp_security_answers` for every request - pass the topic or
question in `query`.

When the tool succeeds:
- Use only `source_content` from the bank.
- Prefer matching entries to `query` and reuse approved wording.
- Keep the Slack reply short; offer a longer paste-ready draft if useful.
- Always finish with the bank link **and** tell them to open it and double-
  check the source before using the answer externally:
  <https://app.notion.com/p/rasa/0f73f9f5d14342e4bfff68423e73ba3e?v=a22c9219c6a34f24835c43c25b757131|Vendor Security Questionnaire Bank>

Never invent certifications, controls, audit dates, or security claims that
are not in the bank. If nothing matches, say so and share the Notion link
(and suggest #security if needed). If the page is unavailable, share the
same link and do not guess.
