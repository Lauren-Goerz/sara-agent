---
name: helpdesk_intake
description: >
  Raise a Rasa Wrangle ticket when someone needs a person to action a
  request rather than an answer: VPN or account access, a laptop or
  hardware issue, a new software tool or seat, Salesforce/Gong changes,
  a security or compliance request, a Payhawk or finance question, or a
  private People/HR matter. Activate only when the request needs a ticket.
  Ordinary Ops/HR questions that Sara can answer use their own skills, swag
  uses swag_request, and Zoom licenses use policy_video_conferencing.
---

Wrangle is the only ticketing system at Rasa. Every ticket is created, claimed,
and resolved in Wrangle. There is no helpdesk Slack channel and no Notion
helpdesk board — never point anyone to either.

For every new top-level helpdesk request, call `create_helpdesk_ticket` once
with:
- `request_text`: the employee's full request text
- `team`: exactly one of these Wrangle inbox keys:
  - `ops` — General / Ops request (default when unsure)
  - `it` — IT Support (VPN, laptop, Slack/Google access, YubiKey hardware)
  - `software` — Software request (new tool, seat, Zoom license)
  - `finance` — Payhawk / Finance
  - `hr` — People / HR Issues (pay, performance, personal matters)
  - `swag` — Rasa Swag
  - `revops` — Rev Ops (Salesforce, Gong, and similar)
  - `security` — Security and Compliance
- `is_sensitive_hr`: true when the content should not be repeated publicly
  (People / HR private matters)

General / Ops (`team=ops`) and Payhawk / Finance (`team=finance`) also pass:
- `priority`: Critical, High, Normal, or Low (default Normal)

Those inboxes map like this:
- Ticket name ← short summary
- Priority ← Critical / High / Normal / Low
- Create ticket on behalf of ← Slack requester
- Full message body is stored as the ticket description for agents

Rasa Swag (`team=swag`) and Rev Ops (`team=revops`) map like this (no
priority field):
- Ticket name ← short summary
- Describe the issue ← full request text
- Create ticket on behalf of ← Slack requester

IT Support (`team=it`) also pass:
- `request_category`: one of Account Access, Hardware Issue, Laptop Issue,
  Other, Software Issue, Technical Difficulties
- `urgency`: Urgent, Not Urgent, or Timely (default Timely)
- `anything_else`: optional extra notes if the employee mentioned them

IT field mapping:
- Summary of Request ← short summary
- Detailed description ← full request text
- Request Category ← request_category
- Anything else? ← anything_else
- Urgency ← urgency
- Create ticket on behalf of ← Slack requester

Security and Compliance (`team=security`) also pass:
- `priority`: Critical, High, Normal, or Low (default Normal; Security
  Incident defaults to High if unset)
- `request_category`: Customer Questionnaire, General Enquiry, or Security
  Incident
- `deadline`: optional YYYY-MM-DD if the employee gave a due date

Security field mapping:
- Summary ← short summary
- Detailed Description ← full request text
- Priority ← Critical / High / Normal / Low
- Request Category ← request_category
- Deadline ← deadline (optional)
- Create ticket on behalf of ← Slack requester

Software request (`team=software`) also pass:
- `priority`: Critical, High, Normal, or Low (default Normal)
- `reason`: why they need the tool/seat (required when known)
- `cost`: monthly or annual cost as numbers only — strip $, €, and words
  (leave empty if unknown; do not invent a price)

Software field mapping:
- Ticket name ← short summary
- Describe the issue ← full request text
- Priority ← Critical / High / Normal / Low
- The reason please ← reason
- Monthly or annual cost ← cost (numbers only)
- Create ticket on behalf of ← Slack requester

Do not call the tool again for thread follow-ups once a ticket already exists
for this request (the tool returns `already_ticketed` if so).

When the tool succeeds:
- Post one short Slack reply: confirm the ticket, share `ticket_url` as a
  Slack link, name the inbox (`team_label`), and include `suggested_reply`
  as a draft agents can edit (label it clearly as a suggested reply).
- If `is_sensitive_hr` / `privacy_warning` is set, keep the public reply
  minimal - do not restate private details.

If the tool returns `needs_manual_wrangle`, or if creation failed, tell them to
run `/wrangle` in Slack and pick the `team_label` inbox. Never invent a ticket
id, a ticket link, or any other place to file the request.
