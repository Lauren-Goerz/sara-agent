# Sara — skills by domain

What Sara covers today, grouped by domain. Each skill has a one-line
overview and sample questions you can try in Slack.

Authoring notes (tools, memory, routing) live in [AGENTS.md](AGENTS.md).

## Domains

- [People and company](#people-and-company)
- [Pay, leave, and benefits](#pay-leave-and-benefits)
- [Hiring and contractors](#hiring-and-contractors)
- [Berlin office and relocation](#berlin-office-and-relocation)
- [Travel](#travel)
- [IT and security](#it-and-security)
- [Legal and conduct](#legal-and-conduct)
- [Sales and product marketing](#sales-and-product-marketing)
- [Requests](#requests)
- [Slack and announcements](#slack-and-announcements)
- [Light extras](#light-extras)
- [Fallback](#fallback)

---

## People and company

### `lookup_employee`

Who’s Who: identity, role, team, location, manager, contact, fun fact.

- Who is Alan on?
- Who is my manager according to Who’s Who?
- Fun fact about Lauren?

### `lookup_board`

Rasa board of directors.

- Who is on the Rasa board?
- Who are the board members?

### `lookup_company_info`

Legal-entity details: addresses, VAT, IBANs, BIC/SWIFT, registration, phone.

- What is our German VAT number?
- What’s the Berlin office address?
- What IBAN should I put on an invoice?

### `lookup_company_values`

Official company values and how they are defined.

- What are Rasa’s values?
- What are our culture principles?

### `lookup_employee_handbooks`

Official employee handbooks for countries listed on Notion.

- Where is the German employee handbook?
- Is there a handbook for the UK?

---

## Pay, leave, and benefits

### `payroll_payday`

Days until the next Rasa payday, from location / Deel setup.

- When is payday?
- How many days until I get paid?

### `payroll_payslip`

Where to get a payslip / paycheck by country (DATEV, SequoiaOne, eDoc, Xero, email, Deel).
Uses `resolve_payslip_country` plus an ordered block; asks only when country is unset.

- Where do I download my payslip?
- How do I get my paycheck in Germany?

### `default_session_start`

Engine-managed first turn in a new Slack thread: answer the request instead of greeting.

### `payroll_payslip_details`

Questions about what is *on* a payslip (gross/net, tax, wrong amount) → People Ops via `/wrangle`. Sara does not explain amounts.

- Why is my net pay lower this month?
- I think my tax deduction is wrong.

### `policy_vacation`

Vacation / PTO *entitlement* by country, carry-over, holiday half-days, sickness during vacation.

- How many vacation days do I get in Germany?
- Can I carry unused PTO into next year?

### `leave_vacation`

How to *book* vacation / offline days (including overtime or public-holiday make-up), BambooHR, manager notice, OOO.

- How do I request vacation?
- I worked overtime — what do I do?
- What’s the OOO template?

### `leave_balance`

Point people at the BambooHR Slack app for live balances (Sara does not fetch the numbers).

- How many vacation days do I have left?
- Can you request time off for me?

### `leave_sick`

What to do when you yourself are sick, including country-specific notes / certificates and surgery leave.

- I’m sick, what do I do?
- Do I need a doctor’s note in Germany?

### `leave_dependent_care`

Time off to care for a sick child or another relative (parent, partner, sibling). Not own illness or parental leave.

- My kid is sick — do I book a sick day?
- My mum is in hospital — what leave do I take?

### `leave_parental`

Parental / maternity / paternity / adoption leave (confirms country first).

- How much parental leave do I get?
- How do I book maternity leave?

### `lookup_public_holidays`

Public / bank holidays by country or region.

- Is today a public holiday in Bavaria?
- When is the next bank holiday in the UK?

### `benefits`

Employer benefits & perks 2026 (gym, ClassPass, wellness, health allowances).

- Do we have a gym membership?
- What’s the wellness allowance?

### `benefits_remote_budget`

Remote / home-office budget 2026: equipment, coworking, internet/utility, Payhawk.
Bare “costs more than $X” with no category → ask which budget first.

- How do I claim my home-office budget?
- Can I get a coworking desk reimbursed?

### `equity_employee`

Employee equity / options: grants, refresh, vesting, Carta.

- How do options work at Rasa?
- Where do I see my equity in Carta?

### `learning_development`

Education days, L&D budget, courses, conferences, certifications.
6-month budget allocation reminder only when Slack start date is within 6 months
or they ask about early access.

- How many education days do I get?
- What can I spend the L&D budget on?

### `learning_development_product_onboarding`

Getting to know the product: Rasa University signup and prereqs.

- How do I get started with the product?
- How do I sign up for Rasa University?

### `learning_development_mandatory_training`

Mandatory 2026 compliance training: who must complete it, EasyLlama, and the annual courses (Harassment, GDPR, Security InfraSec, EU AI, Occupational Health).

- What mandatory training do I have to do this year?
- Is GDPR training required for interns?
- Where do I complete EasyLlama courses?

---

## Hiring and contractors

### `hiring_contractors`

Hire, renew, or offboard a contractor / freelancer / agency; contractors vs employees. The intake form is only linked when bringing someone new on.

- I want to hire a new contractor, what should I do?
- How do I renew a contractor?
- What’s the difference between a contractor and an employee?

### `policy_signing_authority`

Who should sign employment contracts and other documents, including by country / entity.

- Who should sign an employment contract in Serbia?
- Who can sign for Rasa UK?

---

## Berlin office and relocation

### `office_berlin`

HQ operations: Nuki, desks, Zoom Room TV, visitors, pets, house rules, printing, snacks, packages, lunch, last person out.

- How do I get into the Berlin office?
- Can I bring my dog?
- Something in the office is broken.

### `office_berlin_wifi`

Berlin office Wi-Fi — links the Notion block; **never posts the password**.

- What’s the office Wi-Fi?
- How do I connect in Berlin?

### `office_berlin_fire_safety`

Fire, evacuation, extinguishers, marshals, first aid — answers only from the Fire Safety page.

- Where are the fire extinguishers?
- What do I do if the fire alarm goes off?

### `relocation_germany`

Relocating to Berlin / Germany: package, visas, Anmeldung, Welcome to Berlin.

- What’s in the relocation package?
- How does Anmeldung work?

---

## Travel

### `policy_business_travel`

Booking and spend: flights, hotels, per diem.

- How do I book a work trip?
- What’s the hotel budget?

### `policy_travel_insurance`

Business-trip cover 2026: eligibility, claims, certificates.

- Am I covered if I travel for work?
- How do I get a travel insurance certificate?

### `policy_work_abroad`

Temporary work from another country (not vacation, not permanent relocation).

- Can I work from Spain for a month?
- What’s the digital-nomad / work-abroad policy?

### `policy_part_time`

Working part-time or reduced hours: minimum hours, country benefit notes, and how to request.

- Can I work part time?
- Can I work 30 hours a week?

### `travel_visa_USA`

US B1/B2 visa process from Notion (not needed for US citizens).

- How do I get a US visa for a customer visit?
- Do I need ESTA or a B1?

---

## IT and security

### `it_support_laptop_repairs`

MacBook / laptop damage, Apple Support, replacements, Rajesh / leasing partner.

- My MacBook screen is cracked, what do I do?
- How do I get a replacement laptop?

### `it_support_stolen_laptop`

Stolen work laptop: police report + notify Ops/Security.

- My work laptop was stolen.
- Someone took my MacBook from the train.

### `onboarding_yubikey`

YubiKey / security-key install steps from Notion.

- How do I set up my YubiKey?
- I need the security key install steps.

### `onboarding_yubisneeze`

Undo an accidental YubiKey OTP paste.

- I accidentally pasted a YubiKey code into Slack.
- How do I turn off OTP after a sneeze?

### `security_crowdstrike`

CrowdStrike / Falcon FAQ: what it is, browsing, who has access.

- What is CrowdStrike?
- Can CrowdStrike see my browsing?

### `security_kandji`

Kandji / Iru FAQ: MDM, keystrokes, who has access.

- What is Kandji?
- Does Kandji log my keystrokes?

### `security_incidents`

Live tracker: was Rasa affected by a named CVE / vendor / incident?

- Was Rasa affected by [CVE-…]?
- Are we impacted by the [vendor] incident?

### `policy_ai_tools`

Approved AI tools and usage rules.

- Which AI tools am I allowed to use?
- Can I put customer data into ChatGPT?

### `policy_security_compliance`

Links into the Updated Policies & Procedures hub (IAM, AUP, IR, AppSec, …).

- Where is the acceptable use policy?
- What’s our incident management policy?

### `rfp_security`

Vendor / RFP security questionnaire bank (fallback after dedicated policy skills).

- Do we have SOC 2?
- Can you fill in this security questionnaire?

### `policy_video_conferencing`

Google Meet is default; Zoom licenses via `/wrangle`.

- Do we use Zoom or Meet?
- How do I get a Zoom license?

---

## Legal and conduct

### `policy_links`

Exact official links and contacts for ethics, conduct, legal, IP, deletion,
security ownership, and export-control topics. These policies are linked, not
summarized.

Sample questions:
- "Where is the whistleblower policy?"
- "Who is Rasa's Ethics Officer?"
- "Can we sell Rasa to a customer in this country?"
- "Who should I ask to review an NDA?"
- "Where is the Code of Conduct?"

### `policy_social_media`

Posting about Rasa on LinkedIn / X, personal vs work accounts.

- Can I post about Rasa on LinkedIn?
- Can I have a private Twitter account?

### `policy_sexual_harassment`

Definitions, reporting, investigation process.

- What’s the sexual harassment policy?
- How do I report harassment?

## Sales and product marketing

### `sales_asset_pitch_deck`

Standard L1 pitch deck + Pitch Decks Notion page (talk tracks, other decks).

- Where is the pitch deck?
- Can I have the L1 deck and talk track?

### `sales_asset_proof_points`

Customer metrics, analysts, deploy speed — answers from / uploads the PDF.

- What proof points can I use with a prospect?
- What’s our typical deploy time?

### `sales_asset_success_metrics`

How customers should measure AI agent performance (Notion + customer-safe blog).

- How should a customer measure their AI agent?
- What KPIs do we recommend for containment / CSAT?

### `sales_asset_win_loss`

Win/Loss Analysis Notion page; add notes via @PMM.

- Where are the win/loss notes?
- Where do I add a lost-deal write-up?

### `product_roadmap`

Internal (Jira-synced) and external product roadmap; suggestions to @PMM.

- What’s on the product roadmap?
- Where do I send a roadmap suggestion?

### `redirect_competitive_analysis`

Competitor comparisons → @Alan / Product Marketing (Sara does not invent battle cards).

- How does Rasa compare to Cognigy?
- Do we have a LangChain battle card?

### `redirect_product_docs`

Technical product how-tos → Docs + the docs bot.

- How do I configure a custom action?
- How does CALM handle slots?

---

## Requests

### `helpdesk_intake`

Anything that needs a *person* to action it: classify into a Wrangle inbox (or tell them to run `/wrangle`).

- I need VPN access.
- Can someone add me to Salesforce?
- I need a Payhawk card change.

### `swag_request`

Customer/community via `/wrangle`, events via `#events`, personal via shop.rasa.com.

- I need stickers for a workshop.
- Where’s the Rasa merch shop?

### `design_request`

Creative / design work → Marketing Asana form.

- I need an illustration for a blog post.
- Can Marketing polish this deck?

### `design_brand_colors`

Official Rasa brand palette (names, hex, usage).

- What are our brand colors?
- What’s the hex for Rasa purple?

### `design_phosphor_icon`

Official Phosphor icon as PNG (SVG on request).

- Can I have a settings icon?
- Phosphor icon for calendar, PNG please.

### `event_request`

Event requests → Asana form; follow-ups in `#events`.

- I want to host a meetup.
- Who pays for catering at a community event?

---

## Slack and announcements

### `rasa_tools_slack`

How Rasa uses Slack: display name, DMs vs channels, Slack Guidelines.

- What should my Slack name be?
- Should this be a channel or a DM?

### `lookup_all_hands_presentations`

All Hands / townhall / offsite slides and recordings (Jan 2025+). Next date: Thursdays + Google Calendar. Broken links → meeting organizer.

- Where are the latest All Hands slides?
- When is the next All Hands?
- The recording link doesn't work — who do I ask?

### `notify_slack`

Post to an allowed Slack channel (with confirm). Not for HR-sensitive content.

- Can you post this in #announcements?
- Please announce the office closure in #general.

---

## Light extras

### `fun_weather`

City weather via Open-Meteo (no API key).

- What’s the weather in Munich?
- Will it rain in London tomorrow?

### `fun_play_music`

Share a song (Spotify if configured, else Apple Music).

- Play Never Gonna Give You Up.
- Put on some jazz.

### `fun_send_gif`

Workplace-safe Giphy into the thread.

- Send a gif of a high five.
- GIF of a cat at a laptop.

### `fun_creator`

Who built Sara (@lauren) and her live age.

- Who built you?
- Are you built by Rasa?

### `fun_fact_rasa`

Rotating canned fun facts about the company or product.

- Tell me a fun fact about Rasa.
- Why is it called Rasa?

### `activate_fun_mode`

Light-hearted reply voices (pirate, valley girl, Yoda, …) or back to normal.

- Talk like a pirate.
- List your modes.
- Normal mode please.

---

## Fallback

### `redirect_unknown_work`

Routes genuine Rasa work questions with no dedicated owner or process to
`/wrangle`, without guessing a team or Slack channel.

Sample questions:
- "Who owns pricing questions?"
- "Which channel handles customer escalations?"

### `decline_creative`

Declines off-topic creative, image, or research requests in Sara's short
playful voice.

Sample questions:
- "Write me a poem."
- "Generate an image for me."

### `search_policies`

Notion search when no dedicated skill matches (broad “where is the page about …”).

- Where can I find the page about OKRs?
- Is there a Notion page on onboarding for managers?
