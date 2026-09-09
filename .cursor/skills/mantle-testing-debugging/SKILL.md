---
name: mantle-testing-debugging
description: >
  Tests and debugs Maestro agents: the train → converse loop, reading
  memory and tool activity in the inspector, and mapping observed misbehavior to the
  control lever that fixes it. Use after any change to skills or config, when the
  agent misbehaves in conversation, or when train fails.
license: Apache-2.0
engine: mantle
rasa_version: ">=3.18"
metadata:
  author: rasa
  version: "0.1.2"
  docs-url: https://github.com/RasaHQ/maestro-docs
---

# Testing and debugging a Maestro agent

## The loop

Run after every meaningful edit — it's fast and catches drift early:

```bash
rasa train             # validates and compiles the project into a model
rasa inspect           # browser UI: converse + watch memory/tools live
```

- Fix `rasa train` errors before debugging conversation behavior. On Maestro,
  `rasa train` is the validation gate (`rasa data validate` is not the supported
  workflow here — train already checks the agent definition and skills).
- Prefer `rasa inspect` over `rasa shell` for debugging: it shows memory state,
  active skill, and tool calls per turn. Known beta quirk: `rasa shell` prints the
  welcome message only after the first user input — not a bug in your agent.
- Retrain after ANY change to `skill.md`, `memory.yml`, `responses.yml`,
  `agent.yml`, or `integrations.yml`. Tool body changes in `tools.py` also require
  retraining if signatures/decorators changed.

## Test conversations to run every time

For each skill, walk at minimum:

1. **Happy path** — the goal completes end to end.
2. **Out-of-order user** — give information before being asked ("I lost my card,
   the gold one, send it rush"). The agent should absorb it, not re-ask.
3. **Digression** — switch to another skill mid-way, then return. The original
   skill should resume where it left off.
4. **Correction** — change an earlier answer ("actually it was stolen, not lost").
   Memory should update and branch-scoped instructions should re-scope.
5. **Refusal/uncertainty** — decline a confirmation. Gated tools must NOT fire.
6. **Out of scope** — ask something no skill covers. The agent should say so
   gracefully, not hallucinate a capability.

## Symptom → fix table

Behavioral drift is fixed with control levers (see `mantle-building-skills`), not
by rewriting prose louder. Find the symptom, apply the narrowest fix:

| Symptom | Diagnosis | Fix |
|---|---|---|
| Tool called before its inputs exist | Tool visible too early | `tool_constraints` → `requires:` on the missing memory key |
| Irreversible action without asking | No confirmation before the tool | Prose confirmation + `requires:` on a confirmation memory key (e.g. `order_confirmed`) |
| Wrong workflow branch followed / branches blended | All branches visible in prompt | `if:`/`else:` markers + categorical entry in `memory.yml` |
| Compliance/legal wording paraphrased | LLM generating what must be verbatim | `utter:` trigger + `responses.yml` |
| Steps skipped/reordered where order is the requirement | Prose can't enforce sequence | ordered block for that section (`@block.<id>`), keep the rest prose |
| Skill activates when it shouldn't | Routing on description alone | sharpen `description`; add skill-level `requires:` |
| Skill doesn't activate when it should | Description doesn't match user phrasing | add trigger phrasings to `description` |
| Agent re-asks for known information | Value never landed in memory | tool must `context.memory.set(key, value)`; check the inspector memory panel |
| Sub-skill runs but parent loses the result | Result declared `private` | move the entry to `public` in the sub-skill's `memory.yml` |
| Gated tool never becomes available | `requires:` key never written, or name mismatch | compare the exact key in the constraint vs what the tool sets |
| `rasa train` fails with `undeclared_memory_write` | Tool writes a key not in any `memory.yml` schema | declare the key (with its `type`) in the skill or project `memory.yml` |

Do **not** reach for `ask_confirmation:`, `on_success:`, or `on_failure:` — those
are not supported on the current build.

## Debugging tool failures

- Tool missing from the LLM's list: it's gated by an unmet `requires:` (intended),
  the function isn't in the skill's `tools.py`, or an outside tool wasn't declared in
  `import_tools`. Resolution order is skill-local → shared → MCP; a same-named
  local tool shadows the MCP one.
- Tool crashes: run `rasa inspect` from a terminal and watch the server log — tool
  tracebacks appear there, not in the browser.
- MCP tool unavailable: check the `mcp_servers` entry in `integrations.yml` and
  that the env var URL resolves; then verify the `mcp/<server-id>:<tool-name>`
  spelling in `import_tools`.
- Memory write rejected: the key isn't declared in the skill's (or project's)
  `memory.yml` schema — `rasa train` flags it as `undeclared_memory_write`.
  Declare the key with its `type` and retrain.

## Training failures

`rasa train` errors name the file — fix in this order because later files
reference earlier ones: `integrations.yml` → `agent.yml` → each skill's
`memory.yml`/`responses.yml` → `skill.md`. Frequent causes: a `tool_constraints` or
`utter:` entry referencing a tool/response that doesn't exist; a `requires:` written
as a map instead of a string expression; a tool writing a memory key not declared in
any `memory.yml` (`undeclared_memory_write`); an `if:` marker on a memory entry that
isn't `categorical`; a frontmatter field the build doesn't accept (the examples use
`name`, `description`, `constraints`, `tool_constraints`); an unquoted colon in an
`agent.yml` `rules:` item (quote it or use a `>` folded scalar).

## When behavior is genuinely non-deterministic

If a symptom reproduces only sometimes: reproduce it 3-5 times in `rasa inspect`
before concluding, and capture the memory panel at the failing turn. If a control
lever exists for it, prefer the lever over prompt-wording experiments — levers are
framework-enforced on every run; prose changes shift probabilities.

## Beta caveats

This engine line is in beta. If the observed behavior contradicts this skill or the
docs (`docs-url`, start at llms.txt), trust the running system — the shipped examples
and the `rasa train` error messages are ground truth on this build. Check the docs
for format changes and report the discrepancy to the user rather than silently
working around it.
