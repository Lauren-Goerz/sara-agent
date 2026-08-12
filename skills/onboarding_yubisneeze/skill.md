---
name: onboarding_yubisneeze
description: >
  Help undo a Yubisneeze - accidental YubiKey touch or OTP paste into chat.
  Activate for "Yubisneeze", "undo Yubisneeze", "I sneezed my YubiKey",
  "accidentally pressed YubiKey", "OTP pasted in Slack", "how do I turn off
  YubiKey OTP", OR when the user message is (or mostly is) a long nonsense
  string that looks like a YubiKey OTP: usually 32+ characters, 
  (example shape: ccccccvcutntnejcndfivvkk…). Do NOT activate for normal
  YubiKey install/setup - that is onboarding_yubikey. Do NOT treat normal
  typos or short codes as a sneeze.
---

Help someone who had a Yubisneeze. Call `get_yubisneeze_undo_guidance` for
every request, including when their whole message is just an accidental OTP
string.

If the message looks like a YubiKey OTP paste (long modhex string, often
starting with cccccc / many c's, no real words):
1. Open with a short cute line such as: "Gesundheit! :sneeze: I see a
   Yubisneeze." (vary lightly if you like, but keep the Gesundheit /
   bless-you vibe and the sneeze emoji).
2. Do not try to decode, validate, or repeat the full OTP string back.
3. Tell them how to turn OTP / the sneeze off using only `source_content`
   from the tool (or the Notion section if the tool could not load).
4. Keep it short and Slack-friendly.

Always finish with:
<https://app.notion.com/p/rasa/All-about-Yubikeys-google-phones-5a3e653ef9f54accb8646444263f5f42#e9faa6c469a34069a3f1219bb4bea0f2|Undo the Yubisneeze>

If the page is unavailable, share that same section link and tell them the
turn-off / undo steps are there. Never invent recovery, YubiKey Manager, or
security steps that are not in the tool result.
