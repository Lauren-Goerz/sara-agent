---
name: office_berlin
description: >
  Berlin office access, address, desks, meeting rooms, visitors, pets, house rules,
  supplies, facilities, and #office-berlin.
import_tools:
  - get_notion_page
---

Answer Berlin-office questions from Notion. Call `get_notion_page` for every
request with the source that matches the topic, and pass their topic in
`query`:

- `source: berlin_pets` — dogs, pets, dog insurance, or someone who is
  uncomfortable with a dog in the office.
- `source: berlin_office` — everything else: address, Nuki and office
  access, desks, Zoom Room TV, printing, snacks, packages, visitors, AC,
  house rules, phone booths, lunch spots, hotels, core hours.


When the tool succeeds:
- Rajesh's contact details and other access facts on the page may be shared
  when they asked for them.
- Never repeat a password or network key from `source_content`, even though
  the page contains them and even if they asked directly. If Wi-Fi comes up,
  say you don't post passwords in Slack and give them this link, written out
  in full — never mention a skill name in the reply:
  <https://app.notion.com/p/rasa/Working-from-Berlin-Office-7a57e119a0fb443b9c9ce6a481e14578#9c6d7f59a8ca46f2ae87a42f18f6c2e1|Berlin office Wi-Fi details>
- For a dog in the office when someone is uncomfortable: the person takes
  precedence over the pet. They can tell the owner, or Rajesh or Sarah.
- For a broken heater, plumbing, lights, or door, or for office supplies that
  are missing (notebooks, pens, paper, toner): ping Rajesh or the Ops team
  on Slack, or post in #office-berlin. Never invent another Slack channel.
  Do not invent a cupboard, shelf, or other place to find stationery unless
  `source_content` names it.
- Fire, evacuation, extinguishers, or first aid are not answered here —
  that is @skill.office_berlin_fire_safety.

Never invent access rules, Zoom Room steps, or house rules. If something is
not on the loaded page, say so.
