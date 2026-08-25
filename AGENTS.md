# Sara — Rasa Ops/HR Maestro agent

This directory is **Sara**, Rasa's internal Ops/HR assistant built on
**Rasa Maestro** (`calm_v2`, currently beta). Behaviour is described in natural
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
 the employee stated it out loud (`user_country_confirmed`). A skill whose
 answer would be harmful if the country were wrong gates its tool on
 `requires: session.project.user_country_confirmed` instead of adding its own
 country and confirmation keys.
- `lib/user_location.py` — single resolver for the employee's work country
 (what they said → country already established this conversation → Slack
 *My Location* → Slack timezone), remembered in `project.user_country`. Any
 country-aware skill should call `user_location.resolve(context)` rather than
 keeping its own country patterns or timezone map.
- `lib/notion_sources.py` — registry of allowlisted Notion pages/databases plus
  shared fetch, clean, cache, and query-aware trimming.
- `lib/notion_page_tool.py` — factory for skills that only read one registered
  page. Register the source, then `tools.py` is `notion_page_tool(...)` with
  that skill's tool name, description, and answer/failure instructions. Keep a
  custom `tools.py` when the skill parses sections, confirms country, searches,
  or loads more than one page.
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
| `lookup_benefits` | Employer benefits & perks 2026 (gym, wellness, etc.) from Notion |
| `lookup_employee_equity` | Employee equity / options (grants, refresh, Carta) from Notion |
| `lookup_learning_development` | Learning & Development (education days, L&D budget, recommended uses) |
| `lookup_remote_budget` | Remote / home-office budget 2026 (Berlin, coworking, WFH) |
| `policy_work_abroad` | Working from other countries / temporary work abroad policy |
| `lookup_relocation_germany` | Relocating to Berlin/Germany (Relocation Guide, Welcome to Berlin, Working in Germany) |
| `lookup_berlin_office` | Working from the Berlin office / HQ guidance |
| `policy_security_compliance` | Security/compliance policies — specific hub page link; further Qs to #security |
| `policy_ai_tools` | Using AI Tools at Rasa (approved tools / usage rules from Notion) |
| `lookup_crowdstrike` | CrowdStrike FAQ (what it is, browsing, who has access) |
| `lookup_kandji` | Kandji / Iru FAQ (what it is, keystrokes, who has access) |
| `policy_data_deletion` | Handling Data Deletion Requests — link + ask #security |
| `policy_security_responsibilities` | Who owns what in security — links Information Security Responsibilities |
| `policy_intellectual_property` | Intellectual Property Rights — link + ask #security (no Q&A) |
| `lookup_holidays` | Public/bank holiday lookup by country or region (e.g. Bayern today) |
| `lookup_weather` | City weather forecast via free Open-Meteo API (no key) |
| `play_music` | Share a song link (Spotify if configured, else Apple Music) |
| `lookup_payday` | Days until next Rasa payday from location / Deel setup |
| `lookup_security_incidents` | Security incidents / "was Rasa affected?" from Notion tracker |
| `rfp_security` | Vendor/RFP security questionnaire bank (fallback after policy_* skills; always double-check source) |
| `policy_social_media` | Social media policy (LinkedIn, X/Twitter, personal accounts) |
| `lookup_board` | Who is on the Rasa board (from Notion) |
| `policy_legal_support` | Legal support: point people to Mat Searle (@Mat) |
| `request_swag` | Swag/merch: customer/community via /wrangle, events via #events, personal via shop.rasa.com |
| `request_design` | Creative/design requests → Asana form (Marketing tracks in Asana) |
| `request_event` | Event requests → Asana form; further Qs to #events |
| `policy_video_conferencing` | Google Meet is default; Zoom licenses via /wrangle software request |
| `policy_travel_insurance` | Travel insurance / business-trip cover from Notion (2026) |
| `policy_business_travel` | Business travel booking & spend rules (flights, hotels, per diem) |
| `policy_anti_bribery` | Anti-bribery / anti-corruption / fraud policy — link only; further Qs to the Ethics Officer |
| `policy_anti_slavery` | Anti-slavery / modern slavery policy — links the Notion page |
| `policy_whistleblower` | Whistleblower policy — link only; further Qs to the Ethics Officer |
| `policy_code_of_conduct` | Rasa Code of Conduct — link only; further Qs to People Ops |
| `policy_sexual_harassment` | Sexual harassment policy (definitions, reporting, process) |
| `lookup_employee_handbooks` | Official employee handbooks by country (only countries listed on Notion) |
| `lookup_ethics_officer` | Who is Rasa's Ethics Officer — links the Notion page |
| `lookup_all_hands_presentations` | Links to the All Hands slides/recordings archive |
| `lookup_win_loss_analysis` | Links to the Win/Loss Analysis Notion page; asks people to add notes via @PMM |
| `lookup_product_roadmap` | Links to the Product Roadmap Notion page (Jira sync + external roadmap); points suggestions to @PMM |
| `lookup_pitch_deck` | Standard L1 pitch deck Google Slides link + Pitch Decks Notion page (talk tracks / other decks) |
| `lookup_success_metrics` | Links Notion success metrics page + Lauren's customer-safe blog on measuring AI agent performance |
| `lookup_product_proof_points` | Answers from / uploads the Product Proof Points PDF (customer metrics, analysts, deploy speed) |
| `helpdesk_intake` | #helpdesk: classify IT/Ops/HR, create Wrangle ticket, Notion reporting mirror, AI draft reply |
| `it_support_laptop_repairs` | MacBook / laptop repair process (Apple Support first, then Rajesh paths) |
| `it_support_stolen_laptop` | Stolen work laptop: police report + notify Ops/Security |
| `onboarding_yubikey` | YubiKey / security-key install steps from Notion |
| `onboarding_yubisneeze` | Undo an accidental YubiKey sneeze / OTP paste |
| `leave_check` | Points users to the BambooHR Slack app for leave balances |
| `leave_sick` | What to do when sick; personalizes by Slack timezone/location |
| `leave_vacation` | How to book vacation, offline days, OOO FAQ |
| `policy_vacation` | Country vacation/PTO policy from Slack location + Notion |
| `leave_parental` | Parental leave guidance; confirms Slack location first |
| `design_brand_colors` | Official Rasa brand palette |
| `design_phosphor_icon` | Colored Phosphor icon (PNG default; SVG on request) |
| `search_policies` | Notion company docs (policies, handbook) |
| `notify_slack` | Post to an allowed Slack channel (with confirm) |
| `redirect_competitive_analysis` | Routes competitor comparisons to @Alan / Product Marketing |
| `redirect_product_docs` | Routes technical product questions to Docs + the docs bot |
| `activate_fun_mode` | Light-hearted reply voices (pirate, valley girl, etc.) |
| `faq_creator` | Rotating YAML responses for "Who built you?" → @lauren + live age |
| `faz_fun_fact_rasa` | Canned rotating fun facts about Rasa (company/product) |
| `send_gif` | Search Giphy and post a workplace-safe GIF into the Slack thread |

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

### Helpdesk (hybrid Wrangle + Notion mirror)

Sara can intake `#helpdesk` messages when the channel ID is in
`SLACK_HELPDESK_CHANNELS` (or `SLACK_ALWAYS_REPLY_CHANNELS` as fallback):

1. Classify into a Rasa Wrangle inbox:
   General / Ops, IT Support, Software request, Payhawk / Finance,
   People / HR Issues, Rasa Swag, Rev Ops, or Security and Compliance.
2. Create a **Wrangle** ticket (agents claim/resolve there).
3. Mirror metadata into the **Notion Helpdesk Mirror** DB (reporting only).
4. Reply once with the ticket link + a suggested agent reply.

Ops setup checklist:
- Enable Wrangle API; set `WRANGLE_*` env vars and each `WRANGLE_INBOX_*` id.
- Put `#helpdesk` in `SLACK_HELPDESK_CHANNELS` / always-reply; invite Sara.
- Turn **off** Wrangle auto-create-from-channel-messages on `#helpdesk`.
- Create Notion mirror DB with the properties listed in `.env.example`, share
  with Sara, set `NOTION_HELPDESK_MIRROR_DB_ID`.
- Optional status sync: `python scripts/sync_helpdesk_mirror.py`.

## Where coding-agent guidance lives

Maestro authoring skills are under `.claude/skills/` and `.cursor/skills/`.
Read them before adding or changing skills.

## Ground rules

- Secrets only via env / `${ENV_VAR}` (or `api_key_env` for LLM) — never inline keys.
- Do **not** create CALM v1 files (`domain.yml`, `config.yml`, `data/` NLU).
- Keep each skill focused on one job; add `skills/<name>/` rather than overloading.
- Keep frontmatter `description` concise: positive triggers plus only the closest
  ambiguous exclusions. Do not enumerate the whole skill catalog in `Do NOT`
  clauses. Skill-specific routing and behavior belong in that skill, not duplicated
  as global `agent.yml` rules.

Docs: https://github.com/RasaHQ/maestro-docs
