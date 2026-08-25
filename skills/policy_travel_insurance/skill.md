---
name: policy_travel_insurance
description: >
  Travel Insurances 2026: business-trip coverage, eligibility, claims, and
  certificates. Not travel booking/spend, temporary work abroad, vacation,
  or general benefits.
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
