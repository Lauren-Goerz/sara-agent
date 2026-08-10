---
name: maestro-configuring-agent
description: >
  Configures the Maestro project config files: agent.yml (identity, persona, rules,
  voice, engine_version), integrations.yml (LLM provider, channels, MCP servers,
  voice providers, storage), memory.yml (schema, cross-skill visibility), and
  responses.yml (verbatim templates). Use when setting up or changing any of these
  files.
license: Apache-2.0
engine: maestro
rasa_version: ">=3.18"
metadata:
  author: rasa
  version: "0.1.1"
  docs-url: https://github.com/RasaHQ/maestro-docs
---

# Configuring a Maestro agent

Project layout:

```
my-agent/
├── agent.yml             # identity, persona, rules, engine_version
├── integrations.yml      # llm provider + channels
├── memory.yml            # optional: project-wide shared memory
├── lib/                  # optional: shared Python imported by tools.py
└── skills/
    └── <skill>/
        ├── skill.md
        ├── tools.py       # skill-local tools, auto-discovered
        ├── memory.yml     # optional: skill-scoped memory schema
        └── responses.yml  # optional
```

Start minimal: `agent.yml` with `engine_version: calm_v2`, `language`, and `persona`,
plus `integrations.yml` with an `llm:` block, is a complete config. Add sections only
when a feature needs them.

## agent.yml — identity and persona

```yaml agent.yml
engine_version: calm_v2
language: en

persona: |
  You are Telco support — a friendly, concise customer service agent.

rules:
- Help with billing and plan questions only.
- >
  Look up the account with the account-lookup tool before quoting a balance:
  never guess a number.

voice:
  enabled: true            # omit or set false for text-only agents
  asr: deepgram_asr        # ids from integrations.yml voice_providers
  tts: deepgram_tts
```

- Keys are **top-level** today — not nested under an `agent:` block.
  `engine_version: calm_v2` selects the Maestro engine. A future build may nest
  identity fields under an `agent:` block; until then, keep the flat shape the
  scaffold and examples use.
- `persona` replaces what the CALM rephraser prompt did: global tone and identity.
  Keep skill-specific behavior out of it — that belongs in the skill's body.
- `rules` are global do/don't guidance the orchestrator applies across every skill
  (scope limits, tone guards, ordering constraints). Quote any rule containing a
  colon, or write it as a `>` folded scalar — an unquoted colon parses as a YAML
  mapping and breaks `rasa train`.
- `voice` is only needed for voice agents; the `asr`/`tts` values reference provider
  ids declared in `integrations.yml`.

## integrations.yml — providers and infrastructure

Holds the LLM provider and input channels — the model/provider config that CALM
kept in `endpoints.yml` and `credentials.yml`. Use `${ENV_VAR}` interpolation for
secrets (and `api_key_env` for the `llm` block) — never literal keys in the file.

```yaml integrations.yml
llm:
  provider: openai
  model: gpt-5.1
  api_base: https://api.openai.com/v1
  api_key_env: OPENAI_API_KEY    # env var NAME, not ${...}; value read at load time

channels:
  rest: { enabled: true }        # REST input (evaluation / HTTP channel)
  inspector: { enabled: true }   # required for `rasa inspect`
```

`llm` is the single model that drives the agent — one flat block, **not** a
`model_groups` list. `channels` declares input channels here (Maestro has no
`credentials.yml`); `rest` + `inspector` are the minimum for local testing — add
others (e.g. `slack`) to deploy.

The sections below are documented but not exercised by the reference beta build —
add them when a feature needs them and confirm with `rasa train`. They use
`${ENV_VAR}` interpolation for secrets:

```yaml
mcp_servers:
  - id: crm
    url: ${CRM_MCP_URL}

voice_providers:
  asr:
    - id: deepgram_asr
      provider: deepgram
      model: nova-2
      api_key: ${DEEPGRAM_API_KEY}
  tts:
    - id: deepgram_tts
      provider: deepgram
      model: aura-2-thalia-en
      api_key: ${DEEPGRAM_API_KEY}

tracker_store:
  type: postgres
  url: ${TRACKER_URL}

event_broker:
  type: kafka
  url: ${KAFKA_URL}
```

| Section | When you need it |
|---|---|
| `llm` | Always — the single model that drives the agent |
| `channels` | Always — at least `rest` and `inspector` locally; add more to deploy |
| `mcp_servers` | A skill imports `mcp/<server-id>:<tool-name>` |
| `voice_providers` | `agent.yml` has `voice.enabled: true` |
| `tracker_store` / `event_broker` | Production persistence/streaming; omit locally |
| `knowledge_sources` | RAG / enterprise search |

Knowledge sources (RAG) are documented but not exercised by the reference beta build
— validate against your build. They are vector stores accessed from tools via
`context.knowledge["<id>"].search(query)`:

```yaml
knowledge_sources:
  - id: billing_docs
    type: vector_store
    provider: pinecone
    index: billing-help-en
    api_key: ${PINECONE_API_KEY}
    top_k: 4
```

## memory.yml — state schema

A skill's own state lives in `skills/<skill>/memory.yml`; state shared across skills
lives in a project-level `memory.yml` at the agent root (it resolves to the
`project.` namespace). Declare every key a tool writes — `rasa train` rejects
an undeclared `context.memory.set()` with `undeclared_memory_write`.

```yaml skills/card_replace/memory.yml
schema:
  public:                      # readable by other skills; exported on completion
    replacement_reason:
      type: categorical        # categorical + enum_values enables if:/else: branching
      enum_values: [lost, stolen, damaged, not_received]
      description: Why the card is being replaced.
    selected_card_id:
      type: text
      description: Account id of the chosen card.
  private:                     # internal to this skill
    eligibility_checked:
      type: bool
      description: Whether account eligibility was verified.
```

Types: `text`, `bool`, `categorical` (with `enum_values`), `json` — each with a
`description`; add `correctable: true` on a value the customer may revise later. A
project-level `memory.yml` uses the same key/`type`/`description` shape but as flat
top-level keys, without the `schema:`/`public:`/`private:` wrapper (as the reference
example shows).

Design rule: `public` is the skill's API. Another skill gating on
`session.project.authenticated` depends only on that key, not on the auth skill
itself — keep public entries few and stable.

## responses.yml — verbatim text

Lives inside a skill folder. Referenced from `skill.md` (an `utter:` trigger or an
ordered-block `action:` step); the framework delivers the text directly, the LLM
never rewrites it. `{session.<scope>.<key>}` interpolates at delivery time.

```yaml skills/card_replace/responses.yml
responses:
  utter_recording_notice:
    - text: >-
        This interaction may be recorded for quality assurance
        and training purposes.
  utter_replacement_failed:
    - text: >-
        We were unable to process your replacement. A support ticket has
        been created. Reference: {session.card_replace.ticket_id}.
```

Use verbatim responses for wording that must be exact (legal, compliance,
brand-mandated). Everything else stays prose so the agent sounds natural.
Do **not** use `on_success:` / `on_failure:` tool hooks — they are not supported
on the current build; attach mandated wording with `utter:` instead.

## Don't

- Don't put secrets literally in any of these files — `${ENV_VAR}` (or, for the
  `llm` block, `api_key_env`) only.
- Don't put skill behavior in `persona` or global config; behavior belongs in the
  owning skill's `skill.md`.
- Don't create `domain.yml`, `config.yml`, or `credentials.yml` — those are CALM
  files. LLM and channel config live in `integrations.yml`.
- Do declare every memory key a tool writes — undeclared `context.memory.set()`
  writes fail `rasa train` (`undeclared_memory_write`).
- The engine is in beta: if a section is rejected by `rasa train`, check the
  current reference at `docs-url` (llms.txt) and the shipped examples before assuming
  a bug.
