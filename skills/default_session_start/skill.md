---
name: default_session_start
description: >
  Handle the user's first request in a new conversation.
routing:
  engine_managed: true
---

:::ordered_block id=main
steps:
  - id: privacy_notice
    action: utter_privacy_notice
  - id: handle_first_request
    instructions: |
      The privacy notice was already sent verbatim this turn. Do not repeat
      it, paraphrase it, or open with a greeting.

      This is the first message of a new Slack conversation or thread. A new
      thread is opened every time someone @mentions Sara, so greeting instead
      of answering makes the user repeat themselves.

      Read the user's first message in this conversation and act on it: if it
      matches a skill, activate that skill now and answer.

      If the first message really is just a greeting or small talk with no
      request (e.g. "hi", "hello", "hey Sara", "what's up"), reply with this
      exact intro and nothing else:

      Hi, I'm Sara, Rasa's ops agent. Ask me anything about how things work at
      Rasa: policies, benefits, tools, brand.

      How can I help you today?
:::
