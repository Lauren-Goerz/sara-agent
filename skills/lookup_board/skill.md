---
name: lookup_board
description: >
  Who serves on Rasa's board of directors. Not general employee lookup.
import_tools:
  - get_notion_page
---

Answer questions about who is on the Rasa board from the designated Notion
page. Call `get_notion_page` with `source: board` for every request.

When the tool succeeds:
- List the board members from `source_content` only.
- Include roles or affiliations when the page has them.

Never invent names or titles.
