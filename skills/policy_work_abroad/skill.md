---
name: policy_work_abroad
description: >
  Policy for temporarily working from another country: "can I work abroad",
  digital nomad, or working a few weeks/month from a destination. Not
  vacation, business travel, travel insurance, or permanent relocation.
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
