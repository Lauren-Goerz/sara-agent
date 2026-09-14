---
name: helpdesk_intake
description: >
  Create a Wrangle ticket for requests needing human action: Ops, IT, software, Finance,
  People, Rev Ops, Security, or swag.
---

Wrangle is Rasa's only ticketing system. For each new top-level request, call
`create_helpdesk_ticket` once with the full `request_text` and one inbox:

- `ops`: General/Ops, also the default when unsure
- `it`: VPN, access, hardware, laptop, or technical trouble
- `software`: a new tool, seat, or license
- `finance`: Payhawk or Finance
- `hr`: private People/pay/performance matters
- `swag`: merchandise
- `revops`: Salesforce, Gong, or revenue systems
- `security`: security, compliance, incidents, or questionnaires

Pass optional fields only when relevant and known. Set `is_sensitive_hr` for
private People matters. The tool owns field mappings, defaults, validation,
and normalization; never invent missing values.

Do not call the tool again for thread follow-ups once a ticket already exists
for this request (the tool returns `already_ticketed` if so).

When the tool succeeds, confirm the ticket, link `ticket_url`, name
`team_label`, and label `suggested_reply` as an editable draft.
- If `is_sensitive_hr` / `privacy_warning` is set, keep the public reply
  minimal - do not restate private details.

If the tool returns `needs_manual_wrangle`, or if creation failed, tell them to
run `/wrangle` in Slack and pick the `team_label` inbox. Never invent a ticket
id, a ticket link, or any other place to file the request.
