---
name: lookup_relocation_germany
description: >
  Relocating to Berlin / Germany - relocation package, visas, moving
  steps, Welcome to Berlin tips, and working-in-Germany overview. Activate
  for "move to Berlin", "relocate to Germany", "relocation guide",
  "Welcome to Berlin", "Anmeldung", "working in Germany overview", or
  similar. Do NOT activate for temporary work from another country while
  staying employed elsewhere (policy_work_abroad). Do NOT activate for
  business travel (policy_business_travel) or travel insurance
  (policy_travel_insurance). Do NOT activate for working from the Berlin
  office day-to-day (lookup_berlin_office). Do NOT activate for generic
  Notion search when this clearly applies.
---

Help people relocating to Berlin / Germany using Rasa's relocation pages.
Call `get_relocation_germany` for every request - pass their topic in
`query` when known (e.g. "visa", "Anmeldung", "relocation package",
"neighborhoods", "taxes").

On follow-ups, call the tool again with the new `query`.

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.- Always finish by sharing all three related links from `related_urls`
  (or these defaults if missing):
  - <https://app.notion.com/p/rasa/Relocation-Guide-Germany-79de728aadc5486b940bdd79b70235d8|Relocation Guide Germany>
  - <https://app.notion.com/p/rasa/Welcome-to-Berlin-fde61822cf77417c8712380d47fba265|Welcome to Berlin>
  - <https://app.notion.com/p/rasa/Overview-Working-in-Germany-f9ae50b8c6cc438e8e86b4c5dbaff1ac|Overview: Working in Germany>

Never invent visa, immigration, tax, or housing advice. If something is not
on the loaded page, say so and share the three links. If the page is
unavailable, share the same three links and do not guess.
