---
name: mantle-docs
description: >
  Answers questions about Mantle by reading the documentation bundled locally at
  `.rasa/docs/mantle/`. Use for ANY question about how Mantle works — concepts,
  configuration keys, runtime behaviour, guarantees, terminology, project layout,
  "what does X do", "how do I Y", "is Z supported" — and whenever no other Mantle
  skill covers the request. Also use before answering from memory about Rasa: recalled
  knowledge is almost certainly CALM v1, a different engine.
license: Apache-2.0
engine: mantle
rasa_version: ">=3.18"
metadata:
  author: rasa
  version: "0.1.4"
  docs-url: https://rasa-2f7eb63d.mintlify.site
---

# Mantle documentation lookup

`rasa init --engine mantle` bundles the full Mantle documentation into
`.rasa/docs/mantle/`. This skill is how you answer questions from it.

## Answer from the docs, not from memory

Mantle is beta and post-dates your training data. What you recall about "Rasa" is
almost certainly **CALM v1** — a different engine. Flows, slots, `domain.yml`,
`config.yml`, intents, stories, and NLU pipelines **do not exist in Mantle**. An
answer that mentions them is wrong here.

So: read the page. Then state the `Source:` path you used, so the user can check
it. If you answer without reading a page, say so explicitly rather than implying
the answer came from the docs.

## Lookup

**Never read `llms-full.txt` in full — it is ~250 KB (~65k tokens).** Use these:

```bash
# 1. Read one whole page (the usual move) — change only the quoted path
awk -v p="Source: /reference/conditions" \
  '$0==p{f=1;print;next} f&&/^Source: /{exit} f' .rasa/docs/mantle/llms-full.txt

# 2. Find which page documents a term
grep -n "requires_confirmation" .rasa/docs/mantle/llms-full.txt

# 3. Map line numbers to pages, to resolve a grep hit to its page
grep -n "^Source: " .rasa/docs/mantle/llms-full.txt

# 4. The full page index, plus a "Key facts for code generation" cheat-sheet
cat .rasa/docs/mantle/llms.txt
```

Recipe 1 prints exactly one page: it starts at that page's `Source:` line and stops
before the next one, so no other page's content is included. Its final line may be the
following page's `#` heading — ignore it. Match the path exactly; `/skills` and
`/mantle/skills` are different pages, and `/index` (not `/`) is the introduction.
Keep the awk program in single quotes — in double quotes the shell expands `$0`
before awk sees it, and the command then returns nothing instead of failing.

## Which page answers what

Pick the page from this table, then read it with recipe 1. This table is a routing
shortcut; `.rasa/docs/mantle/llms.txt` on disk is authoritative. If a topic is not
listed here, `cat` that file — the docs may have gained pages since this skill
shipped.

**Get Started**

- `/index` — Introduction: What Mantle is, progressive control, what a skill looks like
- `/getting-started` — Getting Started: Install and build your first agent with the Rasa Copilot
- `/skills` — Skills: The building block of every agent

**Building Skills**

- `/concepts/instructions` — Instructions: The plain-language body of a skill
- `/concepts/tools` — Tools: Typed functions a skill can call
- `/concepts/memory` — Memory: Values a skill tracks across a conversation
- `/concepts/references` — References: Knowledge the agent answers questions from (chunked at train time)
- `/concepts/responses` — Responses: Verbatim wording the LLM never rewrites

**Progressive Control**

- `/build-guide/tool-constraints` — Tool Constraints: requires:, requires_confirmation:, on_success:/on_failure:
- `/build-guide/scoped-instructions` — Scoped Instructions: if: markers for deterministic branching
- `/build-guide/ordered-blocks` — Ordered Blocks: Strict sequence control
- `/build-guide/sub-skills` — Sub-skills: Composition via @skill.<id>

**Orchestration**

- `/mantle` — Mantle: The orchestrator
- `/mantle/runtime-loop` — Runtime Loop: Deterministic-first loop
- `/mantle/guarantees` — Guarantees: What the framework enforces
- `/mantle/context` — Context: How Mantle manages conversation context
- `/mantle/skills` — Skills & Routing: Skill selection and stacking

**Reference**

- `/reference/project-structure` — Project structure: Every file and folder an agent recognises, and which are required
- `/reference/conditions` — Conditions: The memory expression language used by requires:, if:, ordered-block step complete_when:, next:
- `/reference/skill-md` — skill.md: Frontmatter properties and body format (incl. skill-level complete_when mapping)
- `/reference/agent-yml` — agent.yml: Identity, persona, rules, prompt tuning, references.chunking
- `/reference/integrations-yml` — integrations.yml: LLM provider, channels, voice ASR/TTS, Langfuse tracing
- `/reference/memory-yml` — memory.yml: Memory schema, types, visibility
- `/reference/responses-yml` — responses.yml: Response templates and interpolation
- `/reference/ordered-block-steps` — Ordered block steps: Step kinds, step fields, branching
- `/reference/tools` — Tools: Tool interface, ToolContext, built-in framework tools
- `/reference/hooks` — Hooks: observe and modify insertion points (runtime invocation not shipped yet)
- `/reference/execution-loop` — Execution Loop: The per-turn loop as a spec
- `/reference/constraint-table` — Constraint Table: Framework vs LLM at each control level
- `/reference/observability` — Observability: The OpenTelemetry traces emitted per turn
- `/reference/metrics` — Metrics: The metrics available for monitoring agents
- `/reference/system-prompt` — System Prompt: Prompt assembly order and agent.yml overrides
- `/reference/prompt-templates` — Prompt templates: The assembled system prompt for each situation, verbatim

**More**

- `/whats-next` — What's Next: Designed but not yet built
- `/changelog` — Changelog: Builder-facing changes per release

## When the bundle is missing

If `.rasa/docs/mantle/` does not exist (offline install, or the download failed),
re-run `rasa tools init docs mantle` in the project. Failing that, the same pages
are online at https://rasa-2f7eb63d.mintlify.site — `/llms.txt` for the index and
`/llms-full.txt` for every page. Do not answer from memory instead.
