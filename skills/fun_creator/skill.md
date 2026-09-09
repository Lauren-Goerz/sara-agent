---
name: fun_creator
description: >
  Sara FAQ answers about who built or created her. Activate for "who built
  Sara", "who made you", "who created you", or "are you built by Rasa".
  Do NOT activate for employee lookups (lookup_employee), Rasa's board
  (lookup_board), company trivia (fun_fact_rasa), or product questions.
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
