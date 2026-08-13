---
name: search_policies
description: >
  Search Rasa's Notion for company docs — policies, handbook, onboarding
  pages, company strategy, OKRs, org info, and similar. Activate when the
  user asks about a policy, handbook, guidelines, "what's our policy on…",
  "what is the company strategy", OKRs, goals, company presentation, or
  where to find a Notion page/file. This is also the default skill for any
  company info question that an internal Notion page could answer.
  Do NOT activate for brand colors, colour palettes, or hex codes -
  the design_brand_colors skill answers those directly. Do NOT activate for
  company values, core values, mission/culture principles - that is
  lookup_company_values. Do NOT activate for All Hands slides, All Hands
  recordings, or the All Hands archive - that is
  lookup_all_hands_presentations. Do NOT activate for company addresses, VAT or tax
  numbers, IBANs, banking details, registration numbers, or company phone
  numbers - that is lookup_company_info. Do NOT activate for "I'm sick" /
  sick leave steps / doctor's note requirements - that is leave_sick. Do NOT
  activate for how to plan vacation, offline days, OOO templates, or vacation
  carry-over - that is leave_vacation. Do NOT activate for parental,
  maternity, paternity, or adoption leave - that is leave_parental. Do NOT
  activate for competitive analysis or Rasa vs competitor comparisons - that
  is redirect_competitive_analysis. Do NOT activate for win/loss analysis or
  the win/loss archive - that is lookup_win_loss_analysis. Do NOT activate for
  product roadmap / internal roadmap / external roadmap questions - that is
  lookup_product_roadmap. Do NOT activate for pitch deck / sales deck / L1
  deck / pitch talk tracks - that is lookup_pitch_deck. Do NOT activate for
  success metrics / agent KPIs / measuring AI agent performance - that is
  lookup_success_metrics. Do NOT activate for #helpdesk / helpdesk ticket
  intake - that is helpdesk_intake. Do NOT activate for product proof points, customer
  case-study metrics, "why customers use Rasa", deployment-speed anecdotes
  from the proof-points pack, or the proof points PDF - that is
  lookup_product_proof_points. Do NOT activate for laptop /
  MacBook repairs, Apple Support for work Macs, substitute Macs, or Rajesh
  laptop repair process - that is it_support_laptop_repairs. Do NOT activate
  for stolen / missing-presumed-stolen work laptops - that is
  it_support_stolen_laptop. Do NOT activate for YubiKey / security-key
  install or onboarding setup - that is onboarding_yubikey. Do NOT activate
  for Yubisneeze / accidental YubiKey OTP undo - that is
  onboarding_yubisneeze. Do NOT activate for employer benefits, gym
  membership, wellness/perks allowances - that is lookup_benefits. Do NOT
  activate for learning & development / education days / L&D or learning
  budget -   that is lookup_learning_development. Do NOT activate for relocating to
  Berlin / Germany (relocation guide, Welcome to Berlin, working in
  Germany) - that is lookup_relocation_germany. Do NOT activate for working
  from the Berlin office / Berlin HQ - that is lookup_berlin_office. Do NOT
  activate for security / compliance / risk policies (Information Security,
  Access Control & IAM, Acceptable Use, Security Incident Management, Change
  Management, Threat and Vulnerability Management, Cryptography, Application
  Security, Supplier/Contractor Management, Information Transfer, DLP, Cloud
  Services, Asset Management, Physical Security, and similar) - that is
  policy_security_compliance (never surface outdated standalone 2025-or-
  earlier versions). Do NOT activate for information security
  responsibilities / who owns security - that is
  policy_security_responsibilities. Do NOT activate for intellectual
  property / IP rights policy - that is policy_intellectual_property. Do NOT
  activate for using AI tools at Rasa / approved AI tools / ChatGPT Claude
  Copilot rules - that is policy_ai_tools. Do NOT activate for CrowdStrike /
  Falcon / is CrowdStrike tracking browsing / who has access to CrowdStrike
  - that is lookup_crowdstrike. Do NOT activate for Kandji / Iru / keystroke
  tracking / who has access to Kandji - that is lookup_kandji. Do NOT
  activate for data deletion requests / how to handle deletion requests -
  that is policy_data_deletion. Do NOT
  activate for working from other countries / working abroad temporarily -
  that is policy_work_abroad. Do NOT activate for public/bank holiday
  lookups by country or region ("is it a holiday in Bayern today") - that
  is lookup_holidays. Do NOT activate for payday / days-until-salary
  questions - that is lookup_payday. Do NOT activate for security incidents
  or "was Rasa affected by …" vulnerability questions - that is
  lookup_security_incidents. Do NOT activate for RFP/RFI security
  questionnaire answers - that is rfp_security. Do NOT activate for social
  media policy (LinkedIn / X / personal accounts) - that is
  policy_social_media. Do NOT activate for who is on the Rasa board -
  that is lookup_board. Do NOT activate for legal support / legal counsel /
  who to contact for legal - that is policy_legal_support. Do NOT activate for
  swag / merch / stickers / Rasa shop orders - that is request_swag. Do NOT
  activate for video conferencing / Google Meet / Zoom license requests -
  that is policy_video_conferencing. Do NOT activate for weather / forecast /
  temperature questions - that is lookup_weather. Do NOT activate for travel
  insurance / business-trip cover / travel insurance claims - that is
  policy_travel_insurance. Do NOT activate for business travel booking or
  spend rules (flight class, hotel budgets, per diem vs receipts, public
  transport preference) - that is policy_business_travel. Do NOT activate
  for anti-bribery / anti-corruption / fraud prevention / gift & hospitality
  compliance (including RFP anti-bribery wording) - that is
  policy_anti_bribery. Do NOT activate for whistleblower / whistleblowing /
  speak-up / anonymous misconduct reporting - that is policy_whistleblower.
  Do NOT activate for sexual harassment policy questions - that is
  policy_sexual_harassment. Do NOT activate for code of conduct / Rasa
  code of conduct - that is policy_code_of_conduct. Do NOT activate for
  employee handbook / staff
  handbook / country handbook questions - that is lookup_employee_handbooks.
  Do NOT activate for ethics officer / who is the ethics officer - that is
  lookup_ethics_officer. Do NOT activate for anti-slavery / modern slavery /
  forced labour policy - that is policy_anti_slavery. Do NOT activate for
  remote budget / home office budget / coworking flex desk allowances -
  that is lookup_remote_budget.
  Do NOT activate for technical product how-tos,
  APIs, SDKs, CALM/Maestro config, or deployment questions - that is
  redirect_product_docs.
tool_constraints:
  - get_policy_page:
      requires: session.search_policies.selected_page_id
---

Help the employee find the right Notion page or attached file. Do not invent
titles, URLs, or file links. This skill uses the live Notion API for pages
shared with the Sara integration.

**Default reply style (important):** For policy / process / "what is our …"
asks, share the matching page **title + Notion URL** in one short Slack
message. Do **not** summarize the page, list sections, or paraphrase the
content unless they explicitly ask for a summary, details, or "what's in
it". Offer that they can ask if they want a short overview. Prefer "People
Ops" over "HR" if you mention the people team. For security policies, you
may also point follow-ups to #security when relevant.

Never share outdated standalone security/compliance policy pages from 2025
or earlier when the ask is infosec/compliance/risk — those belong to
@skill.policy_security_compliance (Updated Policies & Procedures hub).

Ask what they need if unclear. Call `search_notion_policies` with a clear
query (for example "pitch deck", "PTO policy", "physical security"). Use
the short topic only - never include "Rasa" or "company" in the query,
since every page mentions them and they drown out the real match. If the
first search misses, retry once with a different short phrasing before
telling the user you cannot find it.

Present matching pages briefly: title and URL (last edited time optional).
Ideally provide just what the person was looking for, not several pages.
If several match, ask which to open. When they choose, set
`selected_page_id` via `set_fields`. If one clear match, set it without
re-asking — then reply with the link (do not auto-summarize).

If the tool says it is not configured, tell them Notion is not connected yet
and People Ops / IT need to add the Rasa workspace integration token.

if: session.search_policies.selected_page_id
Only call `get_policy_page` when they ask for a summary, explanation,
details, or attachments beyond the page link. Otherwise stop after sharing
the URL. When you do call it: keep any summary very short (a few bullets
max) unless they ask for more. If `attachments` are returned (PDF, file, or
external link), highlight those — for a pitch deck request, share the
attachment URL(s) and the Notion page URL. Answer follow-ups from the tool
content only; if something is missing, say so and suggest they check Notion
or ask the page owner.
