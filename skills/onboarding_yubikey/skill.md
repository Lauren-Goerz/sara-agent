---
name: onboarding_yubikey
description: >
  Onboarding help for installing and setting up a Rasa YubiKey / security key,
  including Google phone related YubiKey guidance from the internal Notion
  page. Activate for "how do I install my YubiKey", "set up YubiKey",
  "Yubikey setup", "security key onboarding", "Google phone YubiKey", or
  "where are the YubiKey instructions". Do NOT activate for undoing a
  Yubisneeze / accidental YubiKey OTP paste - that is onboarding_yubisneeze.
  Do NOT activate for general laptop repairs (it_support_laptop_repairs),
  product docs, or broad Notion search.
---

Help someone install or set up their Rasa YubiKey. Call
`get_yubikey_setup_guidance` for every request.

When the tool succeeds, walk them through the relevant steps from
`source_content` only - keep it short and Slack-friendly. Always finish with:
<https://app.notion.com/p/rasa/All-about-Yubikeys-google-phones-5a3e653ef9f54accb8646444263f5f42|All about Yubikeys / google phones>

If the page is unavailable, share that same Notion link and tell them to
follow the steps there. Never invent PIN, Google account, Slack, or hardware
setup steps that are not in the tool result.
