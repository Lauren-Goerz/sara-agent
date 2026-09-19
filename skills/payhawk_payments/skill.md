---
name: payhawk_payments
description: >
  Payhawk payments and reimbursements: vendor bank transfers, payables email
  routing, personal-fund reimbursement, virtual cards, per diem, and mileage.
  Not which travel spend (flights/hotels) is allowed, and not a named budget
  amount (remote, L&D, travel, gym) alone.
import_tools:
  - get_notion_page
---

Answer Payhawk payment, reimbursement, per diem, and mileage questions from
Notion. Call `get_notion_page` for every request with the source that matches
the topic, and pass their topic in `query`:

- `source: per_diem_mileage` — per diem rates/process, food while travelling,
  mileage / km claims, Deel employees and receipts-only, Serbia mileage or
  per diem via Payhawk.
- `source: payhawk` — everything else: vendor bank transfers, payables emails
  by entity, personal-fund reimbursement (60-day rule), virtual cards, adding
  funds, Serbia reimbursement process (non-mileage).

Example queries: "bank transfer invoice payables", "reimbursement 60 days",
"virtual card add funds", "per diem Germany Payhawk", "mileage claim".

When the tool succeeds:
- Answer from `source_content` only. Use exact payables addresses, deadlines,
  rates, card rules, and contacts from the page — never invent them.
- For vendor / invoice bank transfers, give the entity → payables email (or
  in-app submit) rules from the page. Urgent/special payments: contact Finance
  as the page says.
- For personal-fund reimbursements, cover the submit-within-60-days rule and
  any high-amount / virtual-card exception only if it is on the page.
- Acceptable travel spend for flights, hotels, and class of travel is
  @skill.policy_business_travel — point there when they ask what they may
  book, not how to pay, claim per diem, or submit mileage in Payhawk.
- Remote/home-office, L&D, or gym claim *eligibility and amounts* stay with
  those budget skills; this skill covers Payhawk payment mechanics plus per
  diem / mileage process.

If they only name a dollar amount without saying Payhawk, invoice, payment,
reimbursement, virtual card, per diem, or mileage, do not answer from these
pages — the global budget clarifier applies.

Never invent emails, rates, card balances, approval paths, or contacts. If it
is not on the loaded page, say so and share the Notion link. For Payhawk
access or card issues that need a human, point to `/wrangle` → Payhawk /
Finance.
