---
name: fun_fact_rasa
description: >
  Fun facts about Rasa the company or product - "tell me a fun fact about
  Rasa", "Rasa trivia", "interesting fact about Rasa", origin of the name,
  company history tidbits. Activate for those. Do NOT activate for a fun
  fact about a specific employee (lookup_employee). Do NOT activate for
  "who built you" (who_built_sara) or company values (lookup_company_values).
utter:
  - utter_rasa_fun_fact:
      on: activate
---

Share one fun fact about Rasa. The utter_rasa_fun_fact response has several
canned variations and Maestro picks one at random - deliver it verbatim and
do not add another fact of your own.
