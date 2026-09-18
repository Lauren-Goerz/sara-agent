---
name: policy_links
description: >
  Official links or contacts for ethics/legal policies: anti-bribery, anti-slavery,
  whistleblowing, Code of Conduct, IP, data deletion board link, security ownership, export
  controls or selling to a country, Legal review, contracts/NDAs, @Mat, external
  counsel, or the Ethics Officer. Not who signs a document, and not GDPR request
  process or Privacy Team reply letter templates.
---

Call `get_policy_link` with the matching topic:

- anti-bribery, corruption, fraud, gifts or kickbacks: `anti_bribery`
- modern slavery, forced labour or trafficking: `anti_slavery`
- whistleblowing, anonymous misconduct reports or retaliation: `whistleblower`
- Code of Conduct: `code_of_conduct`
- intellectual property or IPR: `intellectual_property`
- handling GDPR/customer data deletion: `data_deletion`
- who owns a security area: `security_responsibilities`
- sanctions, export classification, or selling/deploying to a country: `export_control`
- contracts, NDAs, legal review, external counsel, or Rasa's lawyer: `legal_support`
- who the Ethics Officer is: `ethics_officer`

Use only the returned `referral` and exact `links`. Do not explain or summarize
policy content. For export controls, never decide whether a country, customer,
partner, or deal is allowed. For whistleblowing, do not press for details.
