---
name: redirect_unknown_work
description: >
  A genuine Rasa work question with no dedicated skill, especially who owns
  pricing, releases, customer escalations, or another internal process.
---

:::ordered_block id=main
steps:
  - id: respond
    action: utter_unknown_work
    next: END
:::
