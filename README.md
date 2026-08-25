# Sara — Rasa Ops/HR Maestro agent

Sara is Rasa’s internal Ops/HR assistant (Slack DMs + `@mention` threads), built on **Rasa Maestro** (`calm_v2`). Behaviour lives in natural language (`agent.yml`, skills), not intents/stories.

## Quick start (local)

```bash
cp .env.example .env   # fill secrets — never commit .env
python -m venv .venv && source .venv/bin/activate
# install Rasa Pro / project deps per your Rasa setup
rasa train
rasa run                # http://localhost:5005
```

For Slack locally, expose the webhook with a tunnel:

```bash
ngrok http 5005
# Slack Event Subscriptions → https://YOUR-NGROK-HOST/webhooks/slack/webhook
```

## Layout

| Path | Purpose |
|---|---|
| `agent.yml` | Persona, global rules |
| `integrations.yml` | LLM + channels |
| `skills/` | One skill per user goal |
| `lib/` | Shared clients (Notion, Slack, Wrangle, …) |
| `.env` | Secrets (`RASA_LICENSE`, Slack, Notion, …) — gitignored |

Authoring notes for coding agents: [AGENTS.md](AGENTS.md).

## Docs

- Maestro: https://github.com/RasaHQ/maestro-docs
