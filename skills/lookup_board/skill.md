---
name: lookup_board
description: >
  Who is on the Rasa board of directors / company board. Activate for "who
  is on the Rasa board", "board members", "board of directors", or similar.
  Do NOT activate for Who's Who employee directory lookups
  (lookup_employee) or company values.
---

Answer questions about who is on the Rasa board from the designated Notion
page. Call `get_rasa_board` for every request.

When the tool succeeds:
- List the board members from `source_content` only.
- Include roles or affiliations when the page has them.
- Keep it short and Slack-friendly.
- Always finish with:
  <https://app.notion.com/p/rasa/Board-984687d72adb4c0fb459c3e9bb280565|Board>

Never invent names or titles. If the page is unavailable, share the same
link and do not guess.
