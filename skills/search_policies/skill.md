---
name: search_policies
description: >
  Search Rasa's Notion for company docs — policies, handbook, pitch decks,
  sales decks, onboarding pages, company strategy, OKRs, roadmaps, org info,
  and similar. Activate when the user asks about a policy, handbook,
  guidelines, "what's our policy on…", "what is the company strategy", OKRs,
  goals, "latest pitch deck", sales deck, company presentation, or where to
  find a Notion page/file. This is also the default skill for any company
  info question that an internal Notion page could answer.
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
  product proof points, customer case-study metrics, "why customers use Rasa",
  deployment-speed anecdotes from the proof-points pack, or the proof points
  PDF - that is lookup_product_proof_points. Do NOT activate for laptop /
  MacBook repairs, Apple Support for work Macs, substitute Macs, or Rajesh
  laptop repair process - that is it_support_laptop_repairs. Do NOT activate
  for stolen / missing-presumed-stolen work laptops - that is
  it_support_stolen_laptop. Do NOT activate for YubiKey / security-key
  install or onboarding setup - that is onboarding_yubikey. Do NOT activate
  for Yubisneeze / accidental YubiKey OTP undo - that is
  onboarding_yubisneeze. Do NOT activate for employer benefits, gym
  membership, wellness/perks allowances - that is lookup_benefits. Do NOT
  activate for working from other countries / working abroad temporarily -
  that is lookup_work_abroad. Do NOT activate for public/bank holiday
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
  travel insurance / business-trip cover / travel insurance claims - that is
  policy_travel_insurance. Do NOT activate for business travel booking or
  spend rules (flight class, hotel budgets, per diem vs receipts, public
  transport preference) - that is policy_business_travel. Do NOT activate for
  remote budget / home office budget / coworking flex desk allowances - that
  is lookup_remote_budget. Do NOT activate for technical product how-tos,
  APIs, SDKs, CALM/Maestro config, or deployment questions - that is
  redirect_product_docs.
tool_constraints:
  - get_policy_page:
      requires: session.search_policies.selected_page_id
---

Help the employee find the right Notion page or attached file. Do not invent
titles, URLs, or file links. This skill uses the live Notion API for pages
shared with the Sara integration.

Ask what they need if unclear. Call `search_notion_policies` with a clear
query (for example "pitch deck", "PTO policy", "remote work"). Use the short
topic only - never include "Rasa" or "company" in the query, since every page
mentions them and they drown out the real match. If the first search misses,
retry once with a different short phrasing before telling the user you cannot
find it. Present matching pages briefly: title, last edited time, and URL.

If they ask for the "latest" of something (e.g. latest pitch deck), prefer
the most recently edited match from the tool results.

Ideally provide just what the person was looking for, not several pages.
If several match, ask which to open. When they choose, set `selected_page_id`
via `set_fields`. If one clear match, set it without re-asking.

If the tool says it is not configured, tell them Notion is not connected yet
and People Ops / IT need to add the Rasa workspace integration token.

if: session.search_policies.selected_page_id
Call `get_policy_page`. Summarize the page body in plain language. If
`attachments` are returned (PDF, file, or external link), highlight those
first — for a pitch deck request, share the attachment URL(s) and the
Notion page URL. Answer follow-ups from the tool content only; if something
is missing, say so and suggest they check Notion or ask the page owner.
