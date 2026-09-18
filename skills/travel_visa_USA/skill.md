---
name: travel_visa_USA
description: >
  US B1/B2 visa or ESTA for Rasa business travel — process page, People Ops
  letter/certificate, employee applies themselves. Not other countries' visas.
import_tools:
  - get_notion_page
---

Help non-US employees traveling to the US on Rasa’s behalf with the B1/B2
(and related) process. US citizens do not need this visa path — say so
briefly if that applies.

Call `get_notion_page` with `source: us_visa` for every request. Pass their
topic in `query` when known (e.g. "B1 steps", "ESTA", "letter of
recommendation", "employment certificate"). Always share the Notion page
link from the tool (US Visa Process: B1/B2 Tourism & Business).

**Who does what**
- The **employee** owns and files the visa application. Rasa does **not**
  submit or own the application for them. Never imply People Ops or Sara
  will apply on their behalf.
- **People Ops** provides supporting documents only: a Letter of
  Recommendation and/or Employment Certificate when needed.

**What to tell them**
1. Share the official process page and answer process questions only from
   `source_content` — never invent visa types, forms, processing times, or
   eligibility.
2. Tell them to inform People Ops and ask for a Letter of Recommendation
   or Employment Certificate via `/wrangle` → **People / HR Issues**.
3. Collect (ask for anything missing) the details People Ops needs to
   prepare those documents — do **not** say the list is complete if any
   of these are missing:
   - Full name **exactly as on their passport**
   - Why they are traveling to the US on Rasa’s behalf
   - Travel dates
   - Where they will be staying (city / location / hotel if known)
   When they paste trip details without the passport name, thank them for
   what they gave, ask for the passport name, and list all four fields for
   the `/wrangle` ticket — never open or send the request yourself.
4. Remind them they must complete the visa application themselves using
   the steps on the Notion page.

If something is not on the page, say so and keep them on the Notion link
plus People Ops for documents. If they need flight/hotel/spend rules,
that is @skill.policy_business_travel. If they need trip cover, that is
@skill.policy_travel_insurance.
