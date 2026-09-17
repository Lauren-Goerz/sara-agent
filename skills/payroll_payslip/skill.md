---
name: payroll_payslip
description: >
  Where to find or download a payslip/paycheck by employment country. Not questions about
  pay amounts or deductions.
---

:::ordered_block id=main
steps:
  # Infer country from this message / Slack / memory before asking.
  - id: resolve_country
    execute_tool: resolve_payslip_country
    next: route_known_country

  # If user_country is already set this session, skip the question.
  - id: route_known_country
    noop: true
    next:
      - if: session.project.user_country == "germany"
        then: payslip_answer_germany
      - if: session.project.user_country == "us"
        then: payslip_answer_us
      - if: session.project.user_country == "france"
        then: payslip_answer_france
      - if: session.project.user_country == "uk"
        then: payslip_answer_uk
      - if: session.project.user_country == "serbia"
        then: payslip_answer_serbia
      - if: session.project.user_country == "india" or session.project.user_country == "other"
        then: payslip_answer_deel
      - else: ask_payslip_country

  # If user_country is not set, ask, then copy the answer into user_country.
  # collect cannot write a project field, so stated_country is a one-step
  # holding place; remember_* immediately promotes it.
  - id: ask_payslip_country
    collect: stated_country
    utterance: utter_ask_payslip_country
    next:
      - if: session.payroll_payslip.stated_country == "germany"
        then: remember_germany
      - if: session.payroll_payslip.stated_country == "us"
        then: remember_us
      - if: session.payroll_payslip.stated_country == "france"
        then: remember_france
      - if: session.payroll_payslip.stated_country == "uk"
        then: remember_uk
      - if: session.payroll_payslip.stated_country == "serbia"
        then: remember_serbia
      - if: session.payroll_payslip.stated_country == "india"
        then: remember_india
      - else: remember_other

  - id: remember_germany
    set_memory:
      user_country: germany
    next: payslip_answer_germany

  - id: remember_us
    set_memory:
      user_country: us
    next: payslip_answer_us

  - id: remember_france
    set_memory:
      user_country: france
    next: payslip_answer_france

  - id: remember_uk
    set_memory:
      user_country: uk
    next: payslip_answer_uk

  - id: remember_serbia
    set_memory:
      user_country: serbia
    next: payslip_answer_serbia

  - id: remember_india
    set_memory:
      user_country: india
    next: payslip_answer_deel

  - id: remember_other
    set_memory:
      user_country: other
    next: payslip_answer_deel

  - id: payslip_answer_germany
    action: utter_payslip_germany
    next: END

  - id: payslip_answer_us
    action: utter_payslip_us
    next: END

  - id: payslip_answer_france
    action: utter_payslip_france
    next: END

  - id: payslip_answer_uk
    action: utter_payslip_uk
    next: END

  - id: payslip_answer_serbia
    action: utter_payslip_serbia
    next: END

  - id: payslip_answer_deel
    action: utter_payslip_deel
    next: END
:::
