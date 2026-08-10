# Sara — Rasa Ops/HR Maestro agent

This directory is **Sara**, Rasa's internal Ops/HR assistant built on
**Rasa Maestro** (`calm_v2`, currently beta). Behaviour is described in natural
language (`agent.yml`, skills), not intents/stories/rules.

Sara lives primarily in **Slack** (DMs + `@mention` threads) and helps with
directory lookups, time off, policies, and announcements. Integrations target
BambooHR, Notion, and Slack (some tools still mock until live credentials are
wired).

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
| `lookup_employee` | BambooHR directory lookup |
| `check_time_off` | PTO balances / time-off requests |
| `search_policies` | Notion company docs (policies, pitch decks, handbook) |
| `notify_slack` | Post to an allowed Slack channel (with confirm) |

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

## Where coding-agent guidance lives

Maestro authoring skills are under `.claude/skills/` and `.cursor/skills/`.
Read them before adding or changing skills.

## Ground rules

- Secrets only via env / `${ENV_VAR}` (or `api_key_env` for LLM) — never inline keys.
- Do **not** create CALM v1 files (`domain.yml`, `config.yml`, `data/` NLU).
- Keep each skill focused on one job; add `skills/<name>/` rather than overloading.

Docs: https://github.com/RasaHQ/maestro-docs
