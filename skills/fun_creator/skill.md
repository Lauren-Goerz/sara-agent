---
name: fun_creator
description: >
  Answer who built or created Sara.
---

Use the ordered block to calculate Sara's current age and send one of the
prewritten FAQ responses from `responses.yml`.

:::ordered_block id=answer_creator_faq
name: fun_creator
description: Calculate Sara's age and send a varied creator FAQ response.
steps:
  - id: calculate_age
    execute_tool: calculate_sara_age
  - id: answer_faq
    action: utter_fun_creator
:::
