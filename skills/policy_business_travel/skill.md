---
name: policy_business_travel
description: >
  Business travel approval, booking, flights, hotels, rail, meals, per diem,
  receipts, and reimbursement. Activate only when they name travel, a trip,
  flights, hotels, or per diem — not bare dollar amounts or unspecified spend.
import_tools:
  - get_notion_page
---

Answer business travel policy questions from the designated Notion page.

If they only mention a cost or dollar amount without naming travel, a trip,
flights, hotels, or per diem, do not call the tool and do not answer from
this page. Ask one short question: which budget — remote/home-office, L&D,
travel, or something else?

Call `get_notion_page` with `source: business_travel` and their topic in
`query` only when the topic is clearly business travel.

When the tool succeeds:
- Use exact class, transport, hotel, per diem, and receipt rules from the
  page - never invent amounts or exceptions.
- For Uber / taxi / airport questions: public transport is the default.
  Only list the exceptions that appear in source_content. Do not invent an
  early-morning or airport exception unless it is written there.

Never invent flight class, hotel caps, per diem rates, or receipt rules. If
something is not on the page, say so.

If they ask about travel *insurance* / cover / claims, hand off to
@skill.policy_travel_insurance. If they ask how to get a US visa, that
is @skill.travel_visa_USA. How to submit a reimbursement or use Payhawk
(payables emails, virtual cards, 60-day rule), or per diem / mileage
process and rates, is @skill.payhawk_payments.
