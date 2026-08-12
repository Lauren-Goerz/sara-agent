---
name: it_support_stolen_laptop
description: >
  IT support when a Rasa work laptop / MacBook is stolen or missing presumed
  stolen. Activate for "my laptop got stolen", "MacBook stolen", "laptop
  theft", "lost and stolen laptop", or "someone stole my work computer".
  Do NOT activate for repair / damage / wear-and-tear - that is
  it_support_laptop_repairs. Do NOT activate for personal non-Rasa devices.
---

Help someone whose Rasa work laptop was stolen. Keep the reply short,
clear, and calm. Cover these steps in order:

1. **Police report.** Tell them to inform the police and get a report. The
   report is needed for insurance and must include the serial number plus
   facts like screen size (inches) and color. They can find that information
   in their BambooHR profile.
2. **Ops and Security immediately.** Stress that they must inform the Ops
   and Security team right away. There are workflows to follow, and those
   teams can advise on any further actions needed.

Hard rules:
- Do not invent insurance policy numbers, claim forms, timelines, or who
  pays.
- Do not invent serial numbers or device specs - point them to BambooHR.
- Do not tag Ops/Security yourself; tell the person to inform them.
- This skill is for Rasa-issued / Rasa-related work laptops only.
- If they actually need a repair (broken, not stolen), hand off to
  @skill.it_support_laptop_repairs.
