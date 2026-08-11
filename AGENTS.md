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
- `lib/` — shared clients (`notion_client`, `slack_client`, `hr_mocks`) and the
  custom Slack channel (`slack_channel.EnvSlackInput`)
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
| `lookup_all_hands_presentations` | Links to the All Hands slides/recordings archive |
| `lookup_win_loss_analysis` | Links to the Win/Loss Analysis Notion page; asks people to add notes via @PMM |
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
