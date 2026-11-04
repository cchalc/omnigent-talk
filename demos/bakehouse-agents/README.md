# One agent, four harnesses: the bakehouse analyst

What this demo shows: the same Omnigent agent (one system prompt, three skills) answering the
same question in **Antigravity (agy)**, then **Claude Code**, **Codex** and **pi**, with every
model call governed and attributed in **Unity Gateway**. agy's Gemini turns go through the
custom `gemini_router` service (80/20 Gemini 3.8 / 3.7 Flash), so the routing split shows too.

## How it's built

| Path | Holds |
| :---- | :---- |
| `agents/prompt.md` | The one system prompt. Each bundle has a copy, checked by `just agents-validate` |
| `agents/bakehouse-<h>/config.yaml` | A bundle per harness: `antigravity-native`, `claude-native`, `codex-native`, `pi` |
| `agents/bakehouse-<h>/skills/*` | Links to `skills/bakehouse-analyst`, `skills/bakehouse-genie`, `skills/gateway-observability` |
| `.agents/skills/*` | The same links, for agy's (and Claude Code's) workspace skill discovery |

- **Why four bundles, not `--harness`:** Omnigent rejects `omni run AGENT --harness <x>-native`.
  A native harness is bound in the spec, so switching harness means switching bundle. The
  prompt and skills are what stay the same.
- **Why a prompt copy, not a link:** Omnigent reads `instructions: prompt.md` only if it
  resolves inside the bundle. A link out of it is read as the literal text `prompt.md`.
  `uv run python -m omnigent_talk.agents sync-prompts` rewrites the copies.
- **Skill links:** Omnigent follows them when it parses a bundle, and its uploader bundles them
  as regular files when they stay inside the Git checkout (checked against the installed
  `omnigent/cli.py`). The three skills come from a separate change; until `skills/` lands, the
  links dangle, `just agents-validate` reports them as pending, and `omni run` refuses to
  upload a bundle with a dangling link.
- **`skills: none`:** the agents see only their three skills, not the presenter's library.

### Attribution: what each harness sends

The contract tags are `{"demo": "bakehouse", "agent_spec": "<bundle>", "harness": "<harness>"}`,
where `<harness>` is the `just agent` name (`agy`, `claude`, `codex`, `pi`). `just agent
<harness>` sets them, but each harness reaches the gateway differently:

| Harness | How the tags get there | Lands as |
| :---- | :---- | :---- |
| agy | `just agent agy` starts the Gemini shim with `AI_GATEWAY_REQUEST_TAGS` and `AI_GATEWAY_AGENT_SPEC`; the shim stamps `Databricks-Ai-Gateway-Request-Tags` and `Databricks-Custom-Coding-Agent: antigravity` on every call. With no settings (a bare `just agy`) it still sends `demo=bakehouse`, `harness=agy`, `agent_spec=unknown` | full contract tags |
| Claude Code | `ANTHROPIC_CUSTOM_HEADERS` carries the tag header; Omnigent keeps it and appends its own attribution | contract tags, plus `pipeline`/`job` |
| Codex, pi | `OMNIGENT_CI_CONTEXT`: Omnigent merges it into the tags on gateway routes, but forwards only its CI keys, so `pipeline` = demo and `job` = agent. Omnigent sends `Databricks-Custom-Coding-Agent` (`codex`, `pi`) by itself | `pipeline`, `job`; harness in `session_metadata.coding_agent` |

The Claude, Codex and pi paths come from reading the installed Omnigent source
(`databricks_ai_gateway.py`, `claude_native/main.py`, `codex_executor.py`,
`pi_native/credentials.py`). Only the agy path has been run (below). On a laptop with
org-managed Claude Code or Codex settings, those calls go to the org gateway, not the demo
workspace (`docs/omni-fevm.md`), so their tags land there too.

## Setup (once)

1. `.env.local` has `DBX_PROFILE`, `CATALOG`, `SCHEMA`, `SHIM_PORT`, `SHIM_KEY`, and the
   Omnigent home and server (`OMNIGENT_CONFIG_HOME`, `OMNIGENT_DATA_DIR`, `OMNI_SERVER`).
   `just agent` reads those from the file and gives `omni` and the shim an explicit
   environment: a short pass-through list (`PATH`, `HOME`, terminal, locale, proxy), the demo
   settings, and the profile as both `DBX_PROFILE` and `DATABRICKS_CONFIG_PROFILE`. Inherited
   routing variables (`ANTHROPIC_*`, `OMNIGENT_*`, `DATABRICKS_HOST`, ...) never reach them. If
   the shell exports a `DBX_PROFILE` or `DATABRICKS_CONFIG_PROFILE` that differs from
   `.env.local`, `just agent` stops rather than pick one.
2. `just agents-print-config` prints the provider entries to add to that Omnigent config. It
   writes nothing. agy takes its endpoint from the **default Gemini provider only**, so the
   `gemini-shim` key provider must be that default (unset `default` on the Databricks Gemini
   provider first). pi needs a workspace provider as its `pi` default.
3. `just agents-validate` shows all four bundles `ok`, with the three skills loaded.
4. The data and Genie agent from the skills change exist: the metric views
   `bakehouse_sales_metrics` and `bakehouse_review_metrics` in the demo schema, and the Genie
   agent "omnigent-talk: Bakehouse analyst".

## Stage runbook (about 6 minutes)

The question, the same in every harness:

> Which franchise had the highest revenue, and what do its reviews say?

| # | Do | Expect | Fallback |
| :---- | :---- | :---- | :---- |
| 1 | `just agent agy` (headline). Ask the question | The shim logs `gemini-3.8-flash -> …gemini_router` lines; agy loads `bakehouse-analyst`, queries the sales metric view, then the review metric view; one-line answer, a table, the SQL | 90 s with no answer: switch to the recording |
| 2 | Exit, then `just agent claude`. Same question | Same skills, same answer shape, Claude Code TUI | 60 s: say "same spec, different harness" and move on |
| 3 | `just agent codex`. Same question | Same | 60 s: move on |
| 4 | `just agent pi`. Same question | Same, on `databricks-claude-sonnet-5-5` | 60 s: move on |
| 5 | Unity Gateway (below) | Calls by agent and harness, the 80/20 split | Pre-captured screenshot |

Before step 1, and whenever an agy session opens:
- **Check agy's model.** The bundle pins `gemini-3.8-flash`, but Omnigent can drop the session
  model on the remote-server path, and agy's own default (Gemini 3.1 Pro) isn't served: the turn
  ends empty with no error. If the status line says 3.1 Pro, run `/model` -> **Gemini 3.8
  Flash** first. The durable fix is the `"model": "Gemini 3.8 Flash (Medium)"` line that
  `just agents-print-config` prints for agy's `settings.json`.
- **Approve tool calls.** Omnigent launches an attended agy without
  `--dangerously-skip-permissions`, so every tool call waits for approval in the terminal or
  the web UI. Approve each one on stage, or pre-trust the workspace in a dry run.

Pass extra `omni run` flags after the harness, e.g. `just agent agy -p "…"` or
`just agent pi --model <gateway model>`.

### What to show in Unity Gateway

Run the traffic **at least an hour before** showing usage: rows can take that long to land.

- **Usage by agent and harness:**
  `databricks experimental aitools tools query demos/bakehouse-agents/usage.sql --profile "$DBX_PROFILE"`
  groups the calls by agent tag and harness, with the served model.
- **Routing split:** in the same output, agy's `gemini_router` calls divide about 80/20
  between Gemini 3.8 and 3.7 Flash (`destination_model`). `just routing-metrics` and the
  routing dashboard (`just dashboard-url`) show it across all demos.
- **Model service config:** `just gateway-show` (destinations, fallback, rate limits).
- **Traces:** the unified trace table is Beta and not yet on the FEVM workspace
  (`docs/research/facts.md`). Show the Omnigent session in the web UI instead.
- **Lineage:** open a metric view in Catalog Explorer and show its upstream tables and the
  queries that read it. Not yet rehearsed: check what the agents' queries add before claiming
  it on stage.

## Known issues

- **pi + Gemini:** pi through the gateway's OpenAI-chat surface fails with HTTP 400. Omnigent's
  pi tool-schema sanitizer (`inner/pi_executor.py`, `_sanitize_schema`) strips `anyOf` and
  friends but passes `type: [X, "null"]` arrays through, and Gemini rejects them. No config
  setting avoids it, so `bakehouse-pi` defaults to `databricks-claude-sonnet-5-5`: direct pi
  needs the serving-endpoint name, and `system.ai.claude-sonnet-5-5` returned 404 there
  (`docs/setup-log.md`, section 6). The fix belongs upstream in Omnigent.
- **agy on Gemini 3.1 Pro:** see "Check agy's model" above. Omnigent swallows the gateway's
  "no unambiguous Gemini model" error, so the only symptom is an empty turn.
- **A process already on `SHIM_PORT`** (e.g. a leftover `just agy-serve`) makes `just agent agy`
  stop, because that shim's tags are unknown. Stop it and rerun.
- **Codex on the demo workspace** needs `ucode configure`, which rewrites the shared `~/.codex`
  (`docs/omni-fevm.md`). Until then Codex calls land on the org gateway.

## Verified

2026-11-03, with the installed omnigent `0.22.0.dev0` and agy `1.5.0`:
- `just agents-validate`: all four bundles parse and validate; harness, name and prompt match.
- The skill links, in a scratch Git checkout with the skills change's `skills/`: Omnigent's
  parser loads all three skills in every bundle, and its uploader (`_bundle`) packs them as
  regular files.
- agy through the shim with this agent's tags, `--model gemini-3.8-flash`: the turn went to
  `gemini_router` (HTTP 200, reply as asked), the background lite call to `gemini_fast`
  (HTTP 200), and the shim logged the tags it stamped. `just gateway-show` shows the 80/20
  destinations; `just probe` returned 200, served by `gemini-3.8-flash`.

Not yet verified: the usage rows for those tags (they lag up to an hour), a full
`just agent <harness>` session for any harness, and whether Claude Code, Codex and pi tags
arrive as the source suggests.
