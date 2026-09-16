# Sara — Rasa Ops/HR agent

Sara is Rasa’s internal Ops/HR assistant in Slack (DMs and `@mention` threads).
She is built on **Rasa Mantle**. Behaviour lives in natural language
(`agent.yml`, skills), not intents or stories.

Answers come from allowlisted Notion pages, a few live lookups (directory,
holidays, All Hands), and Wrangle when someone needs a ticket. She does not
invent Slack channels, and **Wrangle is the only ticketing system**.

Skill catalog with sample questions: [SKILLS.md](SKILLS.md).
Authoring notes live in [AGENTS.md](AGENTS.md).
Regression scenarios live under [eval/](eval/) (run via Rasa MCP /
`rasa tools run`).

## What she can help with

- [People and company](SKILLS.md#people-and-company)
- [Pay, leave, and benefits](SKILLS.md#pay-leave-and-benefits)
- [Hiring and contractors](SKILLS.md#hiring-and-contractors)
- [Berlin office and relocation](SKILLS.md#berlin-office-and-relocation)
- [Travel](SKILLS.md#travel)
- [IT and security](SKILLS.md#it-and-security)
- [Legal and conduct](SKILLS.md#legal-and-conduct)
- [Sales and product marketing](SKILLS.md#sales-and-product-marketing)
- [Requests](SKILLS.md#requests)
- [Slack and announcements](SKILLS.md#slack-and-announcements)
- [Light extras](SKILLS.md#light-extras)

Country-specific answers (payslips, parental leave, vacation) use one shared
work-country for the conversation, remembered for about 60 minutes.

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
# Slack Interactivity Request URL → the same /webhooks/slack/webhook URL
```

Enable **Interactivity & Shortcuts** in the Slack app settings so country
picker button clicks are delivered back to Sara. The custom connector verifies
Slack signatures and continues the active DM or thread conversation.

If a Notion-backed skill starts returning only a link, the page is probably
not shared with the Sara-Agent integration:

```bash
source .venv/bin/activate
python scripts/check_notion_access.py
```

## Layout

| Path | Purpose |
|---|---|
| `agent.yml` | Persona, global rules |
| `integrations.yml` | LLM + channels |
| `memory.yml` | Shared session memory (work country) |
| `skills/` | One skill per user goal |
| `tools/` | Shared tools, including the allowlisted Notion loader |
| `lib/notion_sources.py` | Canonical Notion IDs, URLs, titles, caching, and trimming |
| `lib/` | Shared clients (Notion, Slack, …) |
| `.env` | Secrets (`RASA_LICENSE`, Slack, Notion, …) — gitignored |

## Docs

- Mantle: https://rasa-2f7eb63d.mintlify.site
- Authoring skills (Cursor/Claude): `rasa skills install mantle --yes --ides cursor,claude`
