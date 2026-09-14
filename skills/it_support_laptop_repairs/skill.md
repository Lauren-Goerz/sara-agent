---
name: it_support_laptop_repairs
description: >
  Repair, damage, replacement, or support for a Rasa work laptop. Not theft or personal
  devices.
import_tools:
  - get_notion_page
---

Call `get_notion_page` with `source: laptop_repairs` and the problem as
`query`. Start with Apple Support from `related_slack_links` unless they
already tried it, then the repair option and Rajesh step from
`source_content`. Include the Apple Support link once.

If the correct path depends on whether the Mac is Berlin GmbH, leased, or
purchased from Apple/a reseller, ask which applies before giving that path.

- Do not invent warranty coverage, costs, timelines, or who pays.
- Do not skip the Apple Support first step unless they already completed it.
- Do not tag Rajesh yourself; tell the person to inform him.
- This skill is for Rasa-issued / Rasa-related work Macs only.
