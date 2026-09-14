---
name: fun_fact_rasa
description: >
  Share a fun fact or trivia about Rasa the company or product. Not facts about an
  employee.
utter:
  - utter_rasa_fun_fact:
      on: activate
---

Share one fun fact about Rasa. The utter_rasa_fun_fact response has several
canned variations and Maestro picks one at random - deliver it verbatim and
do not add another fact of your own.
