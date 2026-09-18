---
name: gdpr_data_requests
description: >
  How Rasa handles GDPR data-subject requests: erasure or right to be forgotten,
  rectification, data portability or a copy of data, objecting to processing,
  forward to privacy@rasa.com, one-month deadline, identity checks, or the
  Privacy Team reply letter templates (request for data, deletion confirmation,
  generic no-data response). Not the Handling Data Deletion Requests link-only
  page, and not who signs documents.
import_tools:
  - get_notion_page
constraints:
  - text: >
      Never invent, paraphrase, shorten, or fill in the Privacy Team letter
      templates. Those three letters are only delivered by the skill's
      verbatim actions. Leave every <placeholder> exactly as written.
  - text: >
      Never confirm that anyone's data was deleted, exported, or that a rights
      request was completed. Sara does not action GDPR requests.
---

:::ordered_block id=main
steps:
  - id: classify
    instructions: |
      From the user's latest message, set request_kind with set_fields. Do not
      ask them to pick a category when the message is already clear.

      Use letter_access when they want the Request for Data email / access or
      portability reply template / letter to send when providing data.

      Use letter_deletion when they want the Data Deletion Confirmation email
      template / letter confirming deletion.

      Use letter_generic when they want the Generic Response email template /
      letter for when no personal data was found for that email.

      Use process for how to handle an incoming GDPR request, where to forward
      it, identity checks, deadlines, DPO contact, FAQ, or which systems hold
      data. If they ask for process and a letter in one message, prefer the
      letter kind they named; they can ask for process next.
    complete_when: session.gdpr_data_requests.request_kind
  - id: branch
    noop: true
    next:
      - if: session.gdpr_data_requests.request_kind == "letter_access"
        then: letter_access
      - if: session.gdpr_data_requests.request_kind == "letter_deletion"
        then: letter_deletion
      - if: session.gdpr_data_requests.request_kind == "letter_generic"
        then: letter_generic
      - else: process
  - id: letter_access
    action: utter_gdpr_letter_request_for_data
    next: END
  - id: letter_deletion
    action: utter_gdpr_letter_deletion_confirmation
    next: END
  - id: letter_generic
    action: utter_gdpr_letter_generic_no_data
    next: END
  - id: process
    instructions: |
      Call get_notion_page with source gdpr_data_requests and a focused query
      (for example "forward privacy@rasa.com", "identify subject", "one month",
      "FAQ erasure", "dpo@rasa.com"). Do not use a query that pulls the email
      letter bodies.

      Answer only from source_content, short and Slack-friendly. Cover process
      steps, contacts (privacy@rasa.com, dpo@rasa.com, Security), and deadlines
      that appear on the page.

      If they ask for a reply letter or email template, do not write one. Tell
      them to ask for the Request for Data, Data Deletion Confirmation, or
      Generic Response template by name so it can be delivered verbatim.

      Never paste or rewrite the letter sections from the page. Never say a
      deletion or export was done. If the page does not cover the question,
      say so and point at the Notion link from the tool result.

      After you send the answer, set process_answered to true with set_fields.
    complete_when: session.gdpr_data_requests.process_answered
:::
