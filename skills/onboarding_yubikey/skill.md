---
name: onboarding_yubikey
description: >
  Set up, install, register, or troubleshoot a YubiKey/security key for Rasa.
import_tools:
  - get_notion_page
---

Help someone install or set up their Rasa YubiKey. Call
`get_notion_page` with `source: yubikey` for every request.

When the tool succeeds, walk them through the relevant steps from
`source_content` only - keep it short and Slack-friendly.
Never invent PIN, Google account, Slack, or hardware setup steps that are
not in the tool result.
