# Sara — Rasa Ops/HR agent

Sara is Rasa’s internal Ops/HR assistant in Slack (DMs and `@mention` threads).
She is built on **Rasa Mantle**. 

**Repo:** [rasa-customers/sara-agent](https://github.com/rasa-customers/sara-agent)
(also mirrored on RasaHQ).

Answers come from allowlisted Notion pages and a few live lookups (directory,
holidays, All Hands, Slack profile). When someone needs a human to action a
request, she asks them to fill out a ticket at `/wrangle` —
she does **not yet** create tickets via API. 

Skill catalog with sample questions: [SKILLS.md](SKILLS.md).
Authoring notes live in [AGENTS.md](AGENTS.md).
Regression scenarios live under [eval/](eval/).

## Why not one giant Notion search skill?

We tried that first. The skills in this agent are what remained after plain
Notion search plus tweaks to `agent.yml` stopped being enough.

Often there was too much overlap across pages for search to pick a clear
source. Other times Sara would invent details that were not on the page unless
a skill spelled out how to answer (do this, not that).

So there are many skills on purpose: each one owns a user goal with clear
guidance, usually pinned to a specific Notion source (or a small set of them).
`search_policies` is still there as a broad fallback when nothing else fits.

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
# Install Rasa Pro (private registry) per your Rasa setup, then:
rasa train
rasa inspect            # local Inspector UI
# or Slack:
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
| `agent.yml` | Persona, global rules, session config |
| `integrations.yml` | LLM + channels (REST, Inspector, Slack) |
| `memory.yml` | Shared session memory (work country) |
| `skills/` | One skill per user goal |
| `tools/notion.py` | Shared allowlisted Notion page loader |
| `tools/vacation_sick.py` | Shared leave guidance for sick / dependent / vacation |
| `lib/notion_sources.py` | Notion IDs, URLs, cache, query-aware trimming |
| `lib/user_location.py` | Shared work-country resolver |
| `lib/slack_channel.py` | Slack connector (env secrets, threads, always-reply) |
| `lib/` | Other shared clients (Notion, Slack, …) |
| `scripts/` | `check_notion_access.py`, `rasa_versary.py`, … |
| `eval/` | Small Mantle simulation / regression scenarios |
| `.env` / `.env.example` | Secrets template — never commit `.env` |

## Docs

- Mantle: https://rasa-2f7eb63d.mintlify.site
- Authoring skills (Cursor/Claude): `rasa skills install mantle --yes --ides cursor,claude`
