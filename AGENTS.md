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
- `lib/notion_sources.py` — registry of allowlisted Notion pages/databases plus
  shared fetch, clean, cache, and query-aware trimming. Skills that just read a
  fixed Notion page should register a source here and keep `tools.py` to a thin
  wrapper around `notion_sources.load(...)` rather than re-implementing fetch
  and error handling.
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
| `lookup_remote_budget` | Remote / home-office budget 2026 (Berlin, coworking, WFH) |
| `lookup_work_abroad` | Working from other countries / temporary work abroad policy |
| `lookup_holidays` | Public/bank holiday lookup by country or region (e.g. Bayern today) |
| `lookup_payday` | Days until next Rasa payday from location / Deel setup |
| `lookup_security_incidents` | Security incidents / "was Rasa affected?" from Notion tracker |
| `rfp_security` | RFP/RFI security questionnaire answers from the Notion question bank |
| `policy_social_media` | Social media policy (LinkedIn, X/Twitter, personal accounts) |
| `lookup_board` | Who is on the Rasa board (from Notion) |
| `policy_legal_support` | Legal support: point people to Mat Searle (@Mat) |
| `policy_travel_insurance` | Travel insurance / business-trip cover from Notion (2026) |
| `policy_business_travel` | Business travel booking & spend rules (flights, hotels, per diem) |
| `lookup_all_hands_presentations` | Links to the All Hands slides/recordings archive |
| `lookup_win_loss_analysis` | Links to the Win/Loss Analysis Notion page; asks people to add notes via @PMM |
| `lookup_product_proof_points` | Answers from / uploads the Product Proof Points PDF (customer metrics, analysts, deploy speed) |
| `it_support_laptop_repairs` | MacBook / laptop repair process (Apple Support first, then Rajesh paths) |
| `it_support_stolen_laptop` | Stolen work laptop: police report + notify Ops/Security |
| `onboarding_yubikey` | YubiKey / security-key install steps from Notion |
| `onboarding_yubisneeze` | Undo an accidental YubiKey sneeze / OTP paste |
| `leave_check` | Points users to the BambooHR Slack app for leave balances |
| `leave_sick` | What to do when sick; personalizes by Slack timezone/location |
| `leave_vacation` | How to book vacation, offline days, carry-over, OOO FAQ |
| `leave_parental` | Parental leave guidance; confirms Slack location first |
| `design_brand_colors` | Official Rasa brand palette |
| `design_phosphor_icon` | Colored Phosphor icon (PNG default; SVG on request) |
| `search_policies` | Notion company docs (policies, pitch decks, handbook) |
| `notify_slack` | Post to an allowed Slack channel (with confirm) |
| `redirect_competitive_analysis` | Routes competitor comparisons to @Alan / Product Marketing |
| `redirect_product_docs` | Routes technical product questions to Docs + the docs bot |
| `activate_fun_mode` | Light-hearted reply voices (pirate, valley girl, etc.) |
| `who_built_sara` | "Who built you?" → @lauren + live day count since Aug 11, 2026 |
| `fun_fact_rasa` | Canned rotating fun facts about Rasa (company/product) |

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

## Where coding-agent guidance lives

Maestro authoring skills are under `.claude/skills/` and `.cursor/skills/`.
Read them before adding or changing skills.

## Ground rules

- Secrets only via env / `${ENV_VAR}` (or `api_key_env` for LLM) — never inline keys.
- Do **not** create CALM v1 files (`domain.yml`, `config.yml`, `data/` NLU).
- Keep each skill focused on one job; add `skills/<name>/` rather than overloading.

Docs: https://github.com/RasaHQ/maestro-docs
