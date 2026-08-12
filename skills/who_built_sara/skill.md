---
name: who_built_sara
description: >
  Who built Sara / who made you / who created you / "are you built by Rasa".
  Activate for identity questions about Sara's creator or builder. Do NOT
  activate for Who's Who employee lookups (lookup_employee), company board
  (lookup_board), fun facts about Rasa (fun_fact_rasa), or product/docs
  questions.
---

:::ordered_block id=who_built
name: who_built_sara
description: Pick a varied @lauren creator credit, with a live day count when relevant.
steps:
  - id: calculate_age
    execute_tool: respond_who_built_sara
  - id: say_who_built
    action: utter_who_built_sara
:::
