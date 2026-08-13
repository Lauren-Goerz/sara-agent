---
name: policy_work_abroad
description: >
  Working from other countries / working abroad policy - temporary remote
  work from Denmark, South Africa, or elsewhere, "can I work abroad", "work
  a few weeks from …", "move abroad for a month while working", digital
  nomad / temporary relocation while employed. Activate for those asks.
  Do NOT activate for vacation/PTO booking (leave_vacation), leave balances
  (leave_check), parental leave (leave_parental), travel insurance /
  business-trip cover (policy_travel_insurance), business travel booking /
  spend rules (policy_business_travel), or general Notion search when the
  ask is clearly this policy. Do NOT activate for relocating to Berlin /
  Germany permanently (lookup_relocation_germany).
---

Answer questions about working from other countries using the designated
Notion page. Call `get_work_abroad_guidance` for every request - pass the
destination and duration in `query` when known (e.g. "a few weeks from
Denmark", "one month in South Africa").

When the tool succeeds:
- Answer from `source_content` only, focused on their destination/duration.
- Keep it short and Slack-friendly.
- Include any approval steps, limits, or caveats exactly as on the page.
- Always finish with:
  <https://app.notion.com/p/rasa/Working-from-other-Countries-cd21b2caa0214c85aa2410bb0814e446|Working from other Countries>

Never invent day limits, visa/immigration rules, tax advice, or approvals.
If the answer is not on the page, say so and share the Notion link (and
People Ops if the page points there). If the page is unavailable, share the
same link and do not guess.
