# Sara — Rasa Ops/HR Mantle agent

This directory is **Sara**, Rasa's internal Ops/HR assistant built on
**Rasa Mantle** (currently beta). Behaviour is described in natural
language (`agent.yml`, skills), not intents/stories/rules.

Sara lives primarily in **Slack** (DMs + `@mention` threads) and helps with
directory lookups, time off (via the BambooHR Slack app for now), policies,
and announcements. Integrations target Notion and Slack; BambooHR OAuth can
be re-added later with admin buy-in.

## Project layout

- `agent.yml` — persona, global rules, identity
- `integrations.yml` — LLM + channels (REST, Inspector, Slack)
- `lib/` — shared clients (`notion_client`, `notion_sources`, `slack_client`,
  `hr_mocks`) and the custom Slack channel (`slack_channel.EnvSlackInput`)
- `memory.yml` (project root) — memory shared across skills: the resolved
 `user_country`, how it was established (`user_country_source`), and whether
 the employee stated it out loud (`user_country_confirmed`). `user_country` is
 the one place a person's location lives — never add a per-skill country key
 as a parallel store. A skill whose answer would be harmful if the country
 were wrong (parental leave) gates its tool on
 `requires: session.project.user_country_confirmed`. Project fields are
 write-once per session and can only be written by a tool, a post-write hook,
 or a `set_memory` step — never by the LLM, and `collect:` on a project field
 is rejected at train time. An ordered block that has to ask for the country
 therefore collects into a transient skill entry and immediately promotes it
 with `set_memory: { user_country: <literal> }`; see `payroll_payslip`.
 Session memory clears after `session_config.session_expiration_time`
 (60 minutes, set in `agent.yml`), so a new conversation asks again.
- `lib/user_location.py` — single resolver for the employee's work country
 (what they said → country already established this conversation → Slack
 *My Location* → Slack timezone), remembered in `project.user_country`. Any
 country-aware skill should call `user_location.resolve(context)` rather than
 keeping its own country patterns or timezone map.
- `lib/notion_sources.py` — registry of allowlisted Notion pages/databases plus
  shared fetch, clean, cache, and query-aware trimming.
- `tools/notion.py` — shared `get_notion_page` tool for skills that read
 registered pages. Add `import_tools: [get_notion_page]` to the skill and name
 the exact allowlisted `source` key(s) in its instructions. A skill can name
 several sources and say which topic maps to which, as `office_berlin`
 does — that does not justify a custom tool. Per-source `char_limit` overrides
 live in `_CHAR_LIMITS` there. Keep a custom `tools.py` only when the skill
 parses sections, confirms country, searches, or post-processes the content.
- `tools/vacation_sick.py` — shared `get_vacation_sick_guidance` for
  `leave_sick`, `leave_dependent_care`, and `leave_vacation` (topic =
  sick / dependent_* / vacation / offline / ooo). `policy_vacation` keeps its
  own tool because it also reads Benefits & handbooks.
- `skills/policy_links/` — one deterministic registry for policies Sara only
  links to and never summarizes; add another topic there instead of creating
  another one-link skill.
- `skills/<name>/skill.md` — one skill per user goal
- `skills/<name>/tools.py` — optional `@tool` functions for that skill
- `skills/<name>/memory.yml` — skill-scoped memory schema
- `.env` — secrets (`RASA_LICENSE`, `OPENAI_API_KEY`, Slack, Notion, …). Never commit.

### Skills

| Skill | Purpose |
|---|---|
| `lookup_employee` | Who's Who directory lookup (live Notion database) |
| `lookup_company_info` | Addresses, VAT, banking, and phone details from Notion |
| `lookup_company_values` | Official Rasa company values from Notion |
| `benefits` | Employer benefits & perks 2026 (gym, wellness, etc.) from Notion |
| `equity_employee` | Employee equity / options (grants, refresh, Carta) from Notion |
| `learning_development` | Learning & Development (education days, L&D budget, recommended uses) |
| `learning_development_mandatory_training` | Mandatory 2026 compliance training (EasyLlama, who must complete it, Harassment/GDPR/Security/EU AI/Occupational Health) |
| `learning_development_product_onboarding` | How to get to know the product: Rasa University signup + prereqs |
| `benefits_remote_budget` | Remote / home-office budget 2026 (Berlin, coworking, WFH) |
| `policy_work_abroad` | Working from other countries / temporary work abroad policy |
| `policy_part_time` | Working part-time / reduced hours (min hours, benefits, how to request) |
| `relocation_germany` | Relocating to Berlin/Germany (Relocation Guide, Welcome to Berlin, Working in Germany) |
| `office_berlin` | Working from the Berlin office / HQ: access, Zoom TV, pets, house rules |
| `office_berlin_wifi` | Berlin office Wi-Fi: links the Notion Wi-Fi block; never posts the password in Slack |
| `office_berlin_fire_safety` | Office fire, evacuation, extinguishers, marshals, first aid — answers only from the Fire Safety page, never generic advice |
| `policy_security_compliance` | Security/compliance policies — specific hub page link; further Qs to #security |
| `policy_ai_tools` | Using AI Tools at Rasa (approved tools / usage rules from Notion) |
| `security_crowdstrike` | CrowdStrike FAQ (what it is, browsing, who has access) |
| `security_kandji` | Kandji / Iru FAQ (what it is, keystrokes, who has access) |
| `policy_links` | Exact links/referrals for ethics, conduct, Legal, IP, deletion, security ownership, and export controls |
| `lookup_public_holidays` | Public/bank holiday lookup by country or region (e.g. Bayern today) |
| `fun_weather` | City weather forecast via free Open-Meteo API (no key) |
| `fun_play_music` | Share a song link (Spotify if configured, else Apple Music) |
| `payroll_payday` | Days until next Rasa payday from location / Deel setup |
| `payroll_payslip` | Where to get a payslip/paycheck by country — ordered block plus `resolve_payslip_country`; answers from `project.user_country`, asks only when unset, then writes it back (DATEV, SequoiaOne, eDoc, Xero, email, Deel) |
| `default_session_start` | Engine-managed first turn of a new Slack thread — act on the request instead of greeting |
| `payroll_payslip_details` | Questions about pay contents (gross/net, tax, deductions, wrong pay) → People Ops ticket via `/wrangle`; never explains amounts |
| `security_incidents` | Security incidents / "was Rasa affected?" from Notion tracker |
| `rfp_security` | Vendor/RFP security questionnaire bank (fallback after policy_* skills; always double-check source) |
| `policy_social_media` | Social media policy (LinkedIn, X/Twitter, personal accounts) |
| `lookup_board` | Who is on the Rasa board (from Notion) |
| `policy_signing_authority` | Who should sign employment contracts and other docs by country — Signing Documents Notion page |
| `hiring_contractors` | Hire / renew / offboard contractors and agencies — answers from the Working with Contractors page; hiring requests get the intake form link |
| `swag_request` | Swag/merch: customer/community via /wrangle, events via #events, personal via shop.rasa.com |
| `design_request` | Creative/design requests → Asana form (Marketing tracks in Asana) |
| `event_request` | Event requests → Asana form; further Qs to #events |
| `policy_video_conferencing` | Google Meet is default; Zoom licenses via /wrangle software request |
| `policy_travel_insurance` | Travel insurance / business-trip cover from Notion (2026) |
| `policy_business_travel` | Business travel booking & spend rules (flights, hotels, per diem) |
| `travel_visa_USA` | US B1/B2 visa process from Notion |
| `policy_sexual_harassment` | Sexual harassment policy (definitions, reporting, process) |
| `lookup_employee_handbooks` | Official employee handbooks by country (only countries listed on Notion) |
| `lookup_all_hands_presentations` | All Hands slides/recordings by date (Jan 2025+); next date via calendar; broken links → organizer |
| `sales_asset_win_loss` | Links to the Win/Loss Analysis Notion page; asks people to add notes via @PMM |
| `product_roadmap` | Links to the Product Roadmap Notion page (Jira sync + external roadmap); points suggestions to @PMM |
| `sales_asset_pitch_deck` | Standard L1 pitch deck Google Slides link + Pitch Decks Notion page (talk tracks / other decks) |
| `sales_asset_success_metrics` | Links Notion success metrics page + Lauren's customer-safe blog on measuring AI agent performance |
| `sales_asset_proof_points` | Answers from / uploads the Product Proof Points PDF (customer metrics, analysts, deploy speed) |
| `helpdesk_intake` | Requests needing a ticket: classify into a Wrangle inbox, create the ticket (or point at `/wrangle`), draft an agent reply |
| `it_support_laptop_repairs` | MacBook / laptop repair process (Apple Support first, then Rajesh paths) |
| `it_support_stolen_laptop` | Stolen work laptop: police report + notify Ops/Security |
| `onboarding_yubikey` | YubiKey / security-key install steps from Notion |
| `onboarding_yubisneeze` | Undo an accidental YubiKey sneeze / OTP paste |
| `leave_balance` | Points users to the BambooHR Slack app for leave balances |
| `leave_sick` | What to do when you yourself are sick; personalizes by Slack location |
| `leave_dependent_care` | Caring for a sick child or other relative (not own illness) |
| `leave_vacation` | How to book vacation, offline days (incl. overtime / public holiday), OOO |
| `policy_vacation` | Country vacation/PTO entitlement from Benefits & Perks 2026; carry-over from Vacation and Sick days |
| `leave_parental` | Parental leave guidance; confirms Slack location first |
| `design_brand_colors` | Official Rasa brand palette |
| `design_phosphor_icon` | Colored Phosphor icon (PNG default; SVG on request) |
| `search_policies` | Notion company docs (policies, handbook) |
| `notify_slack` | Post to an allowed Slack channel (with confirm) |
| `rasa_tools_slack` | How Rasa uses Slack: profile name, open channels, Slack Guidelines |
| `redirect_competitive_analysis` | Routes competitor comparisons to @Alan / Product Marketing |
| `redirect_product_docs` | Routes technical product questions to Docs + the docs bot |
| `activate_fun_mode` | Light-hearted reply voices (pirate, valley girl, etc.) |
| `fun_creator` | Rotating YAML responses for "Who built you?" → @lauren + live age |
| `fun_fact_rasa` | Canned rotating fun facts about Rasa (company/product) |
| `fun_send_gif` | Search Giphy and post a workplace-safe GIF into the Slack thread |
| `decline_creative` | Declines off-topic creative/image/research requests with Sara's short cheeky response |
| `redirect_unknown_work` | Unknown genuine Rasa work questions → `/wrangle` without invented ownership |

## Build loop

```bash
source .venv/bin/activate
rasa train             # validate and package models/
rasa inspect           # local Inspector UI
# or Slack locally:
#   ngrok http 5005
#   rasa run
```

Re-run `rasa train` after editing `agent.yml`, `integrations.yml`, or any skill.

### Proactive rasa-versary DMs

Sara does not push messages from skills. Use the daily job that reads each
member's Slack profile **Start date** and DMs them on the anniversary:

```bash
source .venv/bin/activate
python scripts/rasa_versary.py --dry-run   # preview
python scripts/rasa_versary.py            # send
```

Schedule it once a day (cron / launchd / CI). Bot scopes: `users:read`,
`users.profile:read`, `im:write`, `chat:write`. Sent receipts live in
`.data/rasa_versary_sent.json` (gitignored).

### Checking Notion access

A skill answers from Notion only if its page is shared with the Sara-Agent
integration. When a skill starts replying with just a link instead of the
content, check the whole registry:

```bash
source .venv/bin/activate
python scripts/check_notion_access.py
```

Anything listed as not readable needs sharing in Notion (page ⋯ →
Connections → Sara-Agent).

### Ticketing (Wrangle only)

**Wrangle is the only ticketing system.** There is no helpdesk Slack channel
and no Notion helpdesk board — never add either back, in a skill or in prose.

When a request needs a person to action it, `helpdesk_intake` classifies it
into a Wrangle inbox (General / Ops, IT Support, Software request, Payhawk /
Finance, People / HR Issues, Rasa Swag, Rev Ops, Security and Compliance) and
either creates the ticket or tells the employee to run `/wrangle` and pick that
inbox. It is not gated to any channel.

Automatic ticket creation needs the Wrangle API: set the `WRANGLE_*` env vars
and each `WRANGLE_INBOX_*` id. Without them Sara still names the right inbox
and points at `/wrangle`, which is the current behaviour since `WRANGLE_API_KEY`
is unset.

## Where coding-agent guidance lives

Mantle authoring skills are under `.claude/skills/` and `.cursor/skills/`.
Read them before adding or changing skills.

## Ground rules

- Secrets only via env / `${ENV_VAR}` (or `api_key_env` for LLM) — never inline keys.
- Do **not** create CALM v1 files (`domain.yml`, `config.yml`, `data/` NLU).
- Keep each skill focused on one job; add `skills/<name>/` rather than overloading.
- Keep frontmatter `description` concise: positive triggers plus only the closest
  ambiguous exclusions. Do not enumerate the whole skill catalog in `Do NOT`
  clauses. Skill-specific routing and behavior belong in that skill, not duplicated
  as global `agent.yml` rules.

Docs: https://rasa-2f7eb63d.mintlify.site  
Refresh authoring skills after upgrading rasa-pro: `rasa skills install mantle --yes --ides cursor,claude`
