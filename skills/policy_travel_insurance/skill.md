---
name: policy_travel_insurance
description: >
  Rasa travel insurance policy for 2026 - business travel cover, what is
  insured, how to claim, certificates, and related trip-insurance questions.
  Activate for "travel insurance", "am I covered on a work trip", "travel
  insurance claim", "Travel Insurances 2026", or similar. Do NOT activate for
  flight class, hotel budgets, per diem vs receipts, or other booking/spend
  rules - that is policy_business_travel. Do NOT activate for working from
  other countries / temporary work abroad (policy_work_abroad), vacation
  booking (leave_vacation), general benefits/perks (lookup_benefits), or
  generic Notion search when this policy clearly applies.
---

Answer travel insurance questions from the designated Notion page. Call
`get_travel_insurance_policy` for every request - pass their topic in `query`
when known (e.g. "business trip cover", "how to claim", "certificate").

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.
- Use exact coverage, eligibility, and process details from the page - never
  invent or combine them.
- Always finish with:
  <https://app.notion.com/p/rasa/Travel-Insurances-2026-fea448cc42fb4348b4a74f12736c1c50|Travel Insurances 2026>

Never invent coverage limits, claim steps, or certificates. If something is
not on the page, say so and share the Notion link (and whoever the page names
for Ops/People). If the page is unavailable, share the same link and do not
guess.
