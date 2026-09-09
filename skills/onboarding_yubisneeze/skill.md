---
name: onboarding_yubisneeze
description: >
  Undo a Yubisneeze: someone says they accidentally touched their YubiKey or
  pasted an OTP, asks how to turn OTP off, or sends a message that is mostly
  one unbroken run of at least 32 letters from the modhex alphabet
  (c b d e f g h i j k l n r t u v), usually 44 characters and often
  starting with a long row of c's. That 32-character minimum is required:
  when the message is a short string, a lone character, a keyboard mash, a
  typo, an emoji, or a stray accented letter, this skill must not activate
  and something else should handle it. Not normal YubiKey setup
  (onboarding_yubikey).
import_tools:
  - get_notion_page
---

Help someone who had a Yubisneeze. Call `get_notion_page` with
`source: yubisneeze` for every request, including when their whole message is
just an accidental OTP string.

**First, check it really is a sneeze.** Count the characters. It only counts
as an OTP paste when the message is one unbroken run of 32 or more letters
drawn only from `c b d e f g h i j k l n r t u v`, with no spaces and no real
words. A genuine one is about 44 characters — a wall of text, not a few
letters. Anything shorter is not a Yubisneeze, however modhex-looking it is.
A handful of repeated letters is the most common false alarm: treat it as an
ordinary message, not a partial or "starting up" sneeze. There is no such
thing as a small Yubisneeze.

If it falls short of that and they have not described an accidental YubiKey
touch, say nothing about YubiKeys, OTP, or sneezing — do not name the thing
you decided against, and do not give the fix "just in case". Ask what they
need instead, as you would for any unclear message.

If the message really is a YubiKey OTP paste (long modhex string, often
starting with cccccc / many c's, no real words):
1. Open with a short cute line such as: "Gesundheit! :sneeze: I see a
   Yubisneeze." (vary lightly if you like, but keep the Gesundheit /
   bless-you vibe and the sneeze emoji).
2. Do not try to decode, validate, or repeat the full OTP string back.
3. Tell them how to turn OTP / the sneeze off using only `source_content`
   from the tool.
4. Keep it short and Slack-friendly.

Always finish with:
<https://app.notion.com/p/rasa/All-about-Yubikeys-google-phones-5a3e653ef9f54accb8646444263f5f42#e9faa6c469a34069a3f1219bb4bea0f2|Undo the Yubisneeze>

Never invent recovery, YubiKey Manager, or security steps that are not in
the tool result.
