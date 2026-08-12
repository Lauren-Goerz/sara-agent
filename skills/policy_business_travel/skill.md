---
name: policy_business_travel
description: >
  Rasa business travel policy - flight class (economy), public vs private
  transport, hotel cost guidelines (e.g. European city averages), per diem
  vs expenses with receipts, booking rules, and related work-trip spend
  questions. Activate for "business travel policy", "can I book business
  class", "hotel budget", "per diem or receipts", "public transport on
  trips", or similar. Do NOT activate for travel insurance / claims /
  certificates - that is policy_travel_insurance. Do NOT activate for
  working from other countries (lookup_work_abroad), vacation booking
  (leave_vacation), or general benefits (lookup_benefits).
---

Answer business travel policy questions from the designated Notion page.
Call `get_business_travel_policy` for every request - pass their topic in
`query` when known (e.g. "economy flights", "hotel budget Europe",
"per diem vs receipts", "public transport").

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.
- Use exact class, transport, hotel, per diem, and receipt rules from the
  page - never invent amounts or exceptions.
- For Uber / taxi / airport questions: public transport is the default.
  Only list the exceptions that appear in source_content. Do not invent an
  early-morning or airport exception unless it is written there.
- Always finish with:
  <https://app.notion.com/p/rasa/Business-Travel-f5c1d8842db048539e065865d0e066cf|Business Travel>

Never invent flight class, hotel caps, per diem rates, or receipt rules. If
something is not on the page, say so and share the Notion link. If
`used_fallback` is true, still treat `source_content` as the approved policy.

If they ask about travel *insurance* / cover / claims, hand off to
@skill.policy_travel_insurance.
