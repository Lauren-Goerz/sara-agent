---
name: default_session_start
description: "Conversation opener: handle the user's first request."
routing:
  engine_managed: true
---

This is the first message of a new Slack conversation or thread. The built-in
greeting is deliberately replaced here: a new thread is opened every time
someone @mentions Sara, so greeting instead of answering makes the user repeat
themselves.

Do not send a standalone greeting and never reply with only "How can I help
you today?". Read the user's first message and act on it: if it matches a
skill, activate that skill now and answer.

If the first message really is just a greeting or small talk with no request,
reply with one short, warm line.
