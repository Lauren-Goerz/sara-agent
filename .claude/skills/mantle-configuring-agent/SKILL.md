---
name: mantle-configuring-agent
description: >
  Configures the Mantle project config files: agent.yml (identity, persona, rules,
  prompt tuning, session settings, tool_timeout), integrations.yml (LLM model groups, channels
  including voice ASR/TTS, model groups, MCP servers, Langfuse tracing), memory.yml (schema, cross-skill
  visibility), and responses.yml (verbatim templates). Use when setting up or
  changing any of these files, including declaring MCP servers and importing their tools.
license: Apache-2.0
engine: mantle
rasa_version: ">=3.18"
metadata:
  author: rasa
  version: "0.1.12"
  docs-url: https://rasa-2f7eb63d.mintlify.site
---

# Configuring a Mantle agent

Project layout:

```
my-agent/
├── agent.yml              # Required. Identity, persona, rules, prompt tuning
├── integrations.yml       # Required. LLM model groups, channels, optional tracing
├── memory.yml             # Optional. Project-wide shared memory
├── responses.yml          # Optional. Project-wide responses, overrides built-in wording
├── references/            # Optional. Agent-wide knowledge; **/*.md is chunked at train
├── tools/                 # Optional. Shared tools, declared with import_tools
└── skills/
    └── <skill>/           # The folder name is the skill id
        ├── skill.md       # Required. The only required file in a skill
        ├── memory.yml     # Optional. Skill-scoped memory schema
        ├── responses.yml  # Optional. Verbatim wording
        ├── tools.py       # Optional. Skill-local tools, auto-discovered
        ├── tools/         # Optional. Or a folder of them, also auto-discovered
        └── references/    # Optional. Indexed into the same project-wide index
```

Start minimal: `agent.yml` with an `agent:` block carrying `persona`, plus
`integrations.yml` with `llm:`, `model_groups:`, and `channels:` blocks, is a
complete config. Add sections only when a feature needs them. The engine is
selected by project layout, so there is no version key to set.

## agent.yml — identity and persona

```yaml agent.yml
agent:
  id: telco-support
  language: en
  persona: |
    You are Telco support, a friendly and concise customer service agent.

rules:
- Help with billing and plan questions only.
- >
  Look up the account with the account-lookup tool before quoting a balance:
  never guess a number.

prompts:
  text_rules: |
    Plain sentences only. No markdown or bullet lists.

session_config:
  session_expiration_time: 60
```

The file has **two levels**, and mixing them up is the most common mistake:

- Inside `agent:`: `id`, `language`, `persona`. An `agent:` block is required, and
  `persona` must be a non-empty string inside it. A file with no `agent:` block
  fails to load with `config.agent.missing_section`; a missing persona fails with
  `config.agent.missing_persona`.
- **Top-level siblings** of `agent:`: `rules`, `prompts`, `references`,
  `conversation`, `tool_timeout`, `session_config`. Nesting these inside `agent:`
  means they are never read, and unknown keys are ignored rather than rejected,
  so the mistake is silent.

Notes:

- `persona` sets global tone and identity.
- `rules` are global do/don't guidance rendered into every prompt (scope limits,
  tone guards, ordering constraints). Quote any rule containing a colon followed by
  a space, or write it as a `>` folded scalar; an unquoted colon parses as a YAML
  mapping and breaks the load.
- `prompts` overrides individual sections of the system prompt: `text_rules`,
  `voice_rules`, `ack_rule`, `ack_reminder`, `ack_enabled`, `ack_examples`,
  `routing_no_active_skill`. Leave one unset to keep its built-in default.
- `tool_timeout` is an optional wall-clock limit in seconds for local `@tool`
  calls (default `10`). Imported MCP tools use the same value when the server
  omits its own `tool_timeout` in `integrations.yml`.
- `id` is generated and written back into the file when absent.

## integrations.yml — models and infrastructure

Holds the model groups, the input channels customers reach the agent through,
optional MCP servers, and optional Langfuse tracing. Never put a literal key in
this file. Use `api_key_env` on a model entry, where it names an environment
variable and works for every provider. `${ENV_VAR}` expansion happens in the
`channels:` and `mcp_servers:` blocks, which are read with environment variables
expanded; `llm:` and `model_groups:` are not.

```yaml integrations.yml
llm:
  model_group: orchestrator

model_groups:
  - id: orchestrator
    models:
      - provider: openai
        model: gpt-5.1
        api_base: https://api.openai.com/v1
        api_key_env: OPENAI_API_KEY  # env var NAME, not ${...}

channels:
  rest: { enabled: true }        # REST input (evaluation / HTTP channel)
  inspector: { enabled: true }   # required for `rasa inspect`

# Langfuse tracing (optional). Install rasa-pro[monitoring], set
# LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY, then uncomment. Keys use ${VAR}
# syntax; they resolve when Langfuse configures at startup, not at YAML load.
# tracing:
#   type: langfuse
#   public_key: ${LANGFUSE_PUBLIC_KEY}
#   private_key: ${LANGFUSE_SECRET_KEY}
#   host: https://cloud.langfuse.com
```

`llm.model_group` selects the group that drives the agent.
`max_prompt_tokens` is the only other supported key under `llm:`. Provider,
model, credentials, and provider-specific settings belong under the selected
group's `models:` list. Inline provider settings under `llm:` fail validation.
Providers `openai`, `azure`, and `self-hosted` have dedicated clients; any other
value is passed to LiteLLM. `tracing` is optional and lives here.

`channels` declares the channels customers reach the agent through. `rest` and
`inspector` are the minimum for local work: `rest` is what the evaluation runner
talks to, and `inspector` is required for `rasa inspect`.

### MCP servers

Declare each remote MCP server under the top-level `mcp_servers` list. The
server `name` becomes part of every imported tool reference:

```yaml integrations.yml
mcp_servers:
  - name: banking
    url: https://banking.example.com/mcp/
    token: ${MCP_BANKING_TOKEN}
    # tool_timeout: 30
```

Use at most one auth strategy per server: `token`, `api_key`, `oauth`, or
`module`. Secrets must use `${ENV_VAR}` references. `tool_timeout` overrides the
top-level `agent.yml` default for this server.

An MCP server declaration does not expose all of its tools. Each skill
allowlists only the tools it needs in `skill.md`:

```yaml skills/check_balance/skill.md
---
name: Check balance
description: Look up a customer's account balance.
import_tools:
  - mcp/banking:get_balance
---

Ask for the account number, then call @tool.get_balance.
```

The import format is `mcp/<server-name>:<tool-name>`. The server name must match
an `mcp_servers` entry; startup fails if the server or imported tool is
unavailable.

### Voice channels

Speech recognition and synthesis are configured **inside the voice channel entry**,
under `asr:` and `tts:`. Each takes a `name:` selecting the engine plus that
engine's own settings:

```yaml integrations.yml
channels:
  browser_audio:
    enabled: true
    server_url: localhost:5005
    asr:
      name: deepgram
      language_map:
        en-US:
          language: en
          model: flux-general-en
      eot_threshold: 0.8
    tts:
      name: deepgram
      language_map:
        en-US:
          model: aura-2-asteria-en
```

Built-in ASR engines: `deepgram`, `azure`. Built-in TTS engines: `deepgram`,
`azure`, `cartesia`, `rime`. The same `asr:` / `tts:` shape applies to every voice
channel, including `jambonz`, `audiocodes`, and `twilio_media_streams`; what
differs is the telephony connection.

### model_groups

Required for the agent LLM and also used by the optional references embedder.
Declare groups once and reference them by id:

```yaml integrations.yml
model_groups:
  - id: orchestrator
    models:
      - provider: openai
        model: gpt-5.1
  - id: reference_embeddings
    models:
      - provider: openai
        model: text-embedding-3-large
```

```yaml agent.yml
references:
  embeddings: reference_embeddings
  chunking:
    chunk_size: 1000
    chunk_overlap: 20
```

The orchestrator group is read from the live project, so changing it needs a
restart. Embeddings groups are read from the packaged snapshot, so changing the
embedding model needs a retrain. Changing `references.chunking` also needs a
retrain.

## Knowledge (RAG)

Put markdown files in a `references/` folder, at the agent root or inside a
skill. At `rasa train`, every `**/*.md` is split into overlapping character
chunks and embedded. The agent then gets the built-in `search_knowledge` tool.
Hits are **sections of the file**, not the whole document. A large FAQ can stay
in one file; you do not need to split it by hand.

Omit `chunking` to use defaults (`chunk_size: 1000`, `chunk_overlap: 20`). Those
values are **characters**, not embedding tokens. Overlap must be smaller than
size; unknown keys under `chunking` fail the load. Keep `chunk_size` well under
the embedder input limit (8192 tokens on Azure OpenAI embeddings and OpenAI
`text-embedding-3-*`).

Both locations feed one index, and a search covers all of it whatever skill is
active, so write each document to stand on its own. Full field table:
`/reference/agent-yml`. Retrieval flow: `/concepts/references`.

## memory.yml — state schema

A skill's own state lives in `skills/<skill>/memory.yml`; state shared across skills
lives in a project-level `memory.yml` at the agent root (it resolves to the
`project.` namespace). Declare every key a tool writes — `rasa train` rejects
an undeclared `context.memory.set()` with `undeclared_memory_write`.

```yaml skills/card_replace/memory.yml
schema:
  public:                      # readable by every other skill, at any time
    replacement_reason:
      type: categorical        # enum_values constrains what the LLM may record
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

Types: `text`, `bool`, `int`, `float`, `list`, `json`, `categorical` (with
`enum_values`), and `any`. Give each a `description`: it is what the LLM sees when
deciding whether to record a value.

Add `llm_settable: true` on a **skill** entry to let the LLM write it. Leave it
off for engine-derived values (eligibility, computed flags). A skill `collect:`
value is settable either way. Both flags are skill-only: a project field with
`llm_settable` or `collect:` fails `rasa train`.

Root `memory.yml` is a flat map (no `schema:` / public / private). The LLM cannot
write it. The first write is a tool, a post-write hook, `seed: true` (project
only, off by default), or a `set:session.project.<entry>=…` button. After that
the value stays set for the session.

```yaml memory.yml
authenticated:
  type: bool
  description: Whether the customer has verified their identity.
caller_phone:
  type: text
  seed: true
  pii: true
  description: Phone number from the voice channel at connect time.
```

Design rule: `public` is the skill's API. Another skill gating on
`session.project.authenticated` depends only on that key, not on the auth skill
itself — keep public entries few and stable.

How you **reference** a declared entry depends on where you write it:
`session.*` in conditions and structured YAML (`requires:`, `if:`, execute
`parameters:`); `@memory.*` in instruction prose; `{session.*}` in
`responses.yml`; bare or qualified keys in `context.memory.get(...)` inside
`tools.py`. See the fully-qualified names table in the memory.yml reference.

## responses.yml — verbatim text

Lives inside a skill folder, or at the agent root to apply project-wide. The
framework delivers the text directly and the LLM never rewrites it.
`{session.<skill_id>.<entry>}` interpolates at delivery time, as does the bare
`{entry}` form for the skill's own values.

Every `responses.yml` merges into one registry keyed by name, so response names are
global. Prefix them with the skill they belong to. Declaring a built-in name such as
`utter_greet` in the project-root file replaces the bundled one.

```yaml skills/card_replace/responses.yml
responses:
  utter_recording_notice:
    - text: >-
        This interaction may be recorded for quality assurance
        and training purposes.
  utter_card_replacement_fee:
    - text: Standard replacement is free.
    - text: A fee applies for lost-card replacement.
      condition: 'session.card_replace.replacement_reason == "lost"'
  utter_replacement_failed:
    - text: >-
        We were unable to process your replacement. A support ticket has
        been created. Reference: {session.card_replace.ticket_id}.
```

Each response name maps to a **list of variants**. At delivery the engine picks
**one** variant: the first whose `condition` is true (YAML order), or the single
**default** variant with no `condition` when none match.

### Conditional variants

Add `condition` on a variant when the **wording** of a response must change with
memory — for example, different replacement-fee copy for lost vs stolen cards.
When any variant is conditioned, exactly **one** variant must omit `condition`
(the fallback). That fallback may sit anywhere in the list.

```yaml
responses:
  utter_card_replacement_fee:
    - text: Standard replacement is free.
    - text: A fee applies for lost-card replacement.
      condition: 'session.card_replace.replacement_reason == "lost"'
    - text: No fee for cards reported stolen.
      condition: 'session.card_replace.replacement_reason == "stolen"'
```

This is different from a skill `utter:` trigger with `when:` in `skill.md`:
`when:` fires a **whole response** once when memory first becomes true;
`condition` on a variant picks **which wording** to deliver each time something
(action step, collect ask, tool outcome, confirmation prompt, `on: activate`,
etc.) resolves that response name. Both use the same
[condition expression grammar](https://rasa-2f7eb63d.mintlify.site/reference/conditions).
Note: `on: activate` selects variants **after** the skill's memory is reset for
the new run, so CRVs on that skill's own fields usually fall through to the
default unless you use project memory, a matching `initial_value`, or a `when:`
trigger for values written after activation.

Only `text`, `metadata`, `condition`, and `buttons:` are permitted on a variant.
`channel:` is not supported. `metadata.rephrase: true` applies to
**whichever variant is selected**, not always the first variant — leave rephrase
off for compliance-sensitive wording. Other `metadata` keys are stored on the
delivered bot message.

### Static buttons

Optional `buttons:` on a variant attach tap targets to collect asks, action steps,
and confirmation prompts. Each button requires `title`; `payload` defaults to
the resolved title. Use plain-text payloads when the LLM should interpret the tap;
use `set:session.<skill_id>.<entry>=<value>` or `set:session.project.<entry>=<value>`
when the tap must write memory directly (`llm_settable` is not required; collect
advances without `set_fields`). The payload must match a button on the latest
agent message. Stale, missing-field, invalid-value, or non-writable taps utter
`utter_set_memory_button_skipped` (override in project `responses.yml`).
Placeholders in titles and payloads resolve like `{session.*}` in `text`.

`rasa train` / `rasa data validate` check every project `responses.yml`: non-empty
`text`, valid conditions, readable memory references, exactly one default when any
variant is conditioned, unknown variant keys (such as `channel:`), malformed
`buttons`, invalid `set:` payloads, and targets the skill cannot write
(`deny_write`). Findings
accumulate across all skill files and the project-root file.

Use verbatim responses for wording that must be exact (legal, compliance,
brand-mandated). Four things reference a response by name:

- a frontmatter `utter:` trigger, with `on: activate` or a `when:` condition
- `on_success:` / `on_failure:` on a `tool_constraints` entry
- `utter_for_confirmation` / `utter_on_user_denial` under `requires_confirmation:`
- an ordered-block `action:` step, or `utterance:` on a `collect:` step

`rasa train` validates every one of those names. Everything else stays prose so the
agent sounds natural.

## Don't

- Don't put secrets literally in any of these files. Use `api_key_env` on model
  entries and `${ENV_VAR}` in `channels:` and `mcp_servers:`.
- Don't nest `rules`, `prompts`, `references`, `conversation`, `tool_timeout`, or
  `session_config` inside the `agent:` block. They are top-level siblings, and
  nesting them is ignored silently.
- Don't put skill behavior in `persona` or global config; behavior belongs in the
  owning skill's `skill.md`.
- Don't create `domain.yml`, `config.yml`, `credentials.yml`, or an
  `endpoints.yml` just for Langfuse — those are CALM files. LLM, channel, and
  Langfuse tracing config live in `integrations.yml`.
- Do declare every memory key a tool writes — undeclared `context.memory.set()`
  writes fail `rasa train` (`undeclared_memory_write`).
- If `rasa train` rejects a section, read the reference page for that file below
  before assuming a bug. Its error names the file and key at fault.

## Further reading

How to read the bundled documentation at `.rasa/docs/mantle/`, and when to reach for
it, is in `AGENTS.md` under **Documentation** — or the **mantle-docs** skill if this
project has no `AGENTS.md`. Never read `llms-full.txt` whole; it is ~250 KB.

Most relevant here — read the page rather than guessing:

- `/reference/project-structure` — Project structure: every file and folder an agent recognises, and which are required
- `/reference/agent-yml` — agent.yml reference: every key, including `references.chunking`, and which are top-level rather than nested
- `/concepts/references` — References: index-time chunking and `search_knowledge`
- `/reference/integrations-yml` — integrations.yml reference: LLM providers, channels, voice ASR/TTS, model groups, MCP servers
- `/concepts/tools` — Import MCP tools (see its MCP tools section): declare a server, then allowlist tools with `import_tools`
- `/reference/memory-yml` — memory.yml reference: skill schema vs project memory, types, access control
- `/reference/responses-yml` — responses.yml reference: templates, conditional variants, static buttons, interpolation, and the four ways a response fires
