---
name: onboarding_yubikey
description: >
  Install or set up a Rasa YubiKey/security key, including Google phone
  guidance and onboarding instructions. Not accidental OTP/Yubisneeze
  recovery, laptop repairs, or product docs.
import_tools:
  - get_notion_page
---

Help someone install or set up their Rasa YubiKey. Call
`get_notion_page` with `source: yubikey` for every request.

When the tool succeeds, walk them through the relevant steps from
`source_content` only - keep it short and Slack-friendly. Always finish with:
<https://app.notion.com/p/rasa/All-about-Yubikeys-google-phones-5a3e653ef9f54accb8646444263f5f42|All about Yubikeys / google phones>

Never invent PIN, Google account, Slack, or hardware setup steps that are
not in the tool result.
