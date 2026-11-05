# Gateway governance: who picks the model gateway, how to enforce it, where to look

Why do some harnesses land on the demo workspace's Unity Gateway while Claude and Codex land on
the org's? This page answers it from the files and the installed code, then says how to enforce a
gateway per harness and where each kind of call shows up.

Public repo: workspace hosts are `<fevm-workspace>` and `<org-gateway>`. Secrets in the files
read here were not copied. Code references are `omnigent/<path>:<line>` in the installed
`omnigent` 0.22.0.dev0. Claims are in `docs/research/facts.md` (Omnigent section, rows that start
"Gateway governance" or cite 2026-11-04). Anything unproved is marked **OPEN**.

## Two kinds of governance

| Kind | Who owns it | Where it lives | Wins when |
| :---- | :---- | :---- | :---- |
| **Device governance** | The org's IT and the `ug`/Isaac tooling | `/Library/Application Support/ClaudeCode/managed-settings.json`, `~/.codex/config.toml` | It is the highest-precedence source for that CLI. No Omnigent setting beats it |
| **Workspace governance** | The workspace admin | Omnigent server and policies, Unity Gateway config, UC grants, budgets | The harness actually sends its call to that workspace's gateway |

The talk point: workspace governance only governs the calls that reach the workspace.

## (a) How each harness's gateway was decided on this laptop

Setup: `OMNIGENT_CONFIG_HOME=~/.omnigent-fevm`, so Omnigent reads
`~/.omnigent-fevm/config.yaml`. Its provider block, with hosts and profile redacted:

```yaml
providers:
  claude:                    {kind: subscription, cli: claude}
  codex-databricks:          {kind: cli-config, cli: codex, model_provider: Databricks, default: true}
  databricks-fevm:           {kind: databricks, profile: <fevm-profile>, default: [anthropic, pi]}
  databricks-gemini-fevm-cjc: {kind: databricks, profile: <fevm-profile>, native_gemini: true, default: true}
```

The daily `~/.omnigent/config.yaml` also carries `harness.claude-native.command: env ... isaac --`
and `harness.codex-native.command: env ... isaac codex --` (launch through the Isaac wrapper), a
`gateway` provider pointing at the org Anthropic surface, and `databricks` (default for `pi`) on
the org profile. `omni-fevm` never reads that file.

### Omnigent's resolution order

`_resolve_provider_for_build` (`runtime/workflow.py:1123`) picks the provider, most explicit first:

1. A binding in the `inference:` block (`inference_config.py:164`, `resolve_bound_provider`). It
   fails loud if the agent's `executor.auth` names a different provider.
2. `executor.auth: {type: provider, name: X}` on the agent spec (`workflow.py:1181-1201`).
3. `executor.auth: {type: databricks, profile}` or a legacy `profile` (`:1202-1222`).
4. The per-family `default` in `providers:` (`:1223-1241`), via `default_provider_for_harness`
   (`onboarding/provider_config.py:1371`). Families: `claude-sdk`, `claude-native` use
   `anthropic`; `codex`, `codex-native`, `openai-agents` use `openai`; `antigravity-native`
   uses `gemini`; `pi` uses its own `pi` scope, then `anthropic`, then `openai`
   (`provider_config.py:158-194`, `:1371-1430`).
5. Ambient detections, then (claude-sdk only) a Claude subscription backed by managed
   credentials (`workflow.py:1242-1258`), then the first usable credential.

Then `configure_agent_harness_with_provider` (`workflow.py:605`) turns the provider into
environment for the harness. What matters is what the *vendor CLI* does with it afterwards.

### `OMNIGENT_DATABRICKS_ORG_PIN` is not a model-gateway pin

It is set in the process environment here. The code says what it does:

- `cli_auth.py:608` defines it as the "`?o=` server URL this process and its children are bound
  to". `load_databricks_org_id` (`cli_auth.py:649`) reads it before the stored server record.
- `host/connect.py:654` forwards it to runners "so runners keep routing to [the workspace]".
- `cli.py:3916-3921` re-derives it for a daemon from the selected server URL.

So it picks the **workspace behind the Omnigent server API** (the `X-Databricks-Org-Id` header,
`cli_auth.py`). It never appears in the env builders for model traffic. It is still worth
scrubbing (the `omni-fevm` wrapper does, `docs/omni-fevm.md`): a stale pin from an agent session
points the daemon's server calls at the wrong workspace. It does not explain Claude or Codex.

### Per harness

| Harness | What chooses the endpoint | Precedence | Evidence |
| :---- | :---- | :---- | :---- |
| **claude-sdk**, **claude-native** | Omnigent sets `ANTHROPIC_BASE_URL` plus an `apiKeyHelper` for the provider (`workflow.py:1378`, `claude_sdk_executor.py:1354`). The `claude` CLI then loads **managed settings**: `env.ANTHROPIC_BASE_URL` (plus `ANTHROPIC_CUSTOM_HEADERS` and the `ANTHROPIC_DEFAULT_*_MODEL` keys) and a top-level `apiKeyHelper` that runs `ug auth-token` | Claude Code settings precedence puts managed settings above everything else, `--settings` included, and an `env` block "follows the levels". Omnigent's own comment agrees: managed settings apply "over the environment omnigent passes" (`onboarding/ambient.py:597-615`) | Rounds 2 and 3 in `docs/omni-fevm.md`: runner log said `base_url=<fevm-workspace>`, no FEVM usage row. The managed file has the keys above (read-only, values not copied). The `claude_managed_gateway` parser (`ambient.py:511-549`) reads the same file |
| **codex**, **codex-native** | The openai-family default is `codex-databricks`, `kind: cli-config` with `model_provider: Databricks` and `default: true`. Omnigent pins `HARNESS_CODEX_MODEL_PROVIDER=Databricks` (`workflow.py:695-721`), which the executor emits as `-c model_provider="Databricks"` (`inner/codex_executor.py:4755`). The provider *table* is read from `~/.codex/config.toml`, which Omnigent copies into the session's private `CODEX_HOME` (`codex_executor.py:1257-1283`). That table has `base_url = <org-gateway>/ai-gateway/codex/v1`, `wire_api = "responses"`, and `auth.command = isaac auth token` | The pin is two layers deep: the Omnigent default selects the name, the Codex file defines what the name means. The file's own top-level `model_provider = "Databricks"` and `[profiles.default]` say the same, so even without Omnigent Codex would use the org gateway | `docs/setup-log.md` §7-9: no FEVM usage row for Codex. Recipe: `~/.omnigent-fevm/config.yaml` and `~/.codex/config.toml` key names above |
| **codex on `databricks-fevm`** | The `databricks` kind uses the signer-backed route (`workflow.py:358-441`). It needs `~/.ucode/state.json` to hold a Codex entry for the workspace (`onboarding/ucode_state.py:145`), and fails with `signer-backed Codex requires configured ucode Codex state; run ucode configure` | Not a precedence problem: nothing is configured | Round 3 in `docs/omni-fevm.md`. The requirement is `~/.ucode/state.json`, not `~/.codex` itself (`ucode configure` is what writes it, and per `omnigent/cli_config.py:3221` it also edits Codex config) |
| **pi** | `databricks-fevm` carries `default: [anthropic, pi]`, so the explicit `pi` scope wins (`provider_config.py:1401`). Pi has no org-managed config on this laptop | Omnigent default, nothing above it | `serving.endpoint_usage` rows (`docs/omni-fevm.md`), and `ai_gateway.usage` rows with `coding_agent = Pi` (see (c)) |
| **agy / antigravity-native** | `databricks-gemini-fevm-cjc` (`native_gemini: true`), the gemini-family default. agy speaks the native Gemini API to the workspace gateway | Omnigent default. agy has no org-managed gateway file here. The SDK harness `antigravity` is different: Gemini API key or Vertex only (`workflow.py:2418-2440`, `:660-668`) | `ai_gateway.usage` rows with `coding_agent = antigravity` |
| **openai-agents** (rory's `qwen` worker) | The agent spec: `executor.auth: {type: databricks, profile}` (`agents/rory/agents/qwen/config.yaml`). Spec auth sits above any family default (`workflow.py:1202`, which returns no provider for openai-agents; `_build_openai_agents_sdk_spawn_env`, `:2086-2210`, then pins `HARNESS_OPENAI_AGENTS_DATABRICKS_PROFILE`) | Spec beats global config. No vendor CLI sits in between, so nothing can override it | Qwen service rows in `demos/routing/metrics.sql` output |

Short version: pi, agy and openai-agents talk to the gateway through Omnigent's own client code,
so Omnigent's choice is the call's destination. Claude and Codex run the vendor CLI, and the CLI
reads a device file that outranks Omnigent.

## (b) How to enforce a gateway per harness

All config below is **printed for the presenter to apply**. This repo never writes
`~/.omnigent*`, `~/.codex`, `~/.claude` or `~/.gemini`.

| # | Layer | Owner | Kind | Enforces |
| :-: | :---- | :---- | :---- | :---- |
| 1 | Omnigent `providers:` with per-family `default` | The user (their config home) | Neither. A user preference | Which provider Omnigent *requests*. Loses to device files for Claude and Codex |
| 2 | Omnigent `inference:` binding | The user, or the managed-sandbox session profile | Workspace, for managed sessions | Provider and model allowlist per harness. Overrides spec auth |
| 3 | Agent spec `executor.auth` | The agent author | Neither | One sub-agent's provider |
| 4 | Agent spec `model_egress` | The agent author | Narrow | Only the signer-backed Databricks Codex route |
| 5 | Omnigent server policies | Workspace admin | Workspace | Which tools and models a session may use. Not which endpoint |
| 6 | Unity Gateway coding-agent config (`ug`, Beta) | Workspace admin | Workspace | The models, MCP servers and tracing for `ug claude` and `ug codex` |
| 7 | Managed-settings file, `~/.codex/config.toml` | Org IT | **Device** | Claude and Codex endpoints, above everything in 1-6 |

### 1. `providers:` with per-family defaults

At most one default per family. This is the fix that put pi and agy on FEVM. For Codex, replace
the `cli-config` default with a `gateway` provider that names the FEVM Codex surface:

```yaml
providers:
  codex-databricks:        # keep it, but no longer the default
    kind: cli-config
    cli: codex
    model_provider: Databricks
  fevm-codex:
    kind: gateway
    default: openai
    openai:
      base_url: https://<fevm-workspace>/ai-gateway/codex/v1
      wire_api: responses
      auth_command: databricks auth token --profile <fevm-profile> | jq -r .access_token
      models: {default: system.ai.gpt-5-5}
```

Why this should work without touching `~/.codex`: a `key`/`gateway`/`local` provider makes
Omnigent generate its own `model_provider` override with the URL and token command
(`codex_native/app_server.py:4195-4262`, `codex_executor.py:2205-2250`), and `-c` overrides
sit above the file's default. `gpt-5-5` and the `/ai-gateway/codex/v1/responses` surface returned
200 on FEVM (`docs/setup-log.md` §6). **OPEN: the end-to-end Codex run on this provider was not
done, because it needs the presenter to edit `~/.omnigent-fevm/config.yaml`.**

A second option, also not run: point Codex at a scratch home. Omnigent honours a user-supplied
`CODEX_HOME` as the source for `auth.json` and `config.toml` (`codex_executor.py:1065-1106`), so
`omni-fevm` could export `CODEX_HOME` to a directory holding a FEVM-only `config.toml`. This
leaves `~/.codex` alone, but the scratch file must carry the provider table itself.

For Claude the same trick cannot work, because the managed file outranks the environment
(`ambient.py:597-615`). A scratch `CLAUDE_CONFIG_DIR` changes the *user* file only. Managed
settings still apply (Claude Code settings precedence, `code.claude.com/docs/en/settings`).

### 2. `inference:` bindings

Authoritative per-harness binding with an allowlist. It is validated by `parse_inference_config`
(`inference_config.py:99`) and read from the same `config.yaml`:

```yaml
inference:
  harnesses:
    codex-native: {provider: fevm-codex, default_model: system.ai.gpt-5-5, model_allowlist: [system.ai.gpt-5-5]}
    claude-sdk:   {provider: databricks-fevm, model_allowlist: [system.ai.claude-sonnet-5-5]}
```

A bound harness refuses an agent whose `executor.auth` names a different provider
(`inference_config.py:171-176`), and a model outside the allowlist raises `ModelNotAllowedError`
(`:37`). The server hands managed sandboxes an immutable session snapshot of this block
(`server/inference_catalog.py`, `host/connect.py:2125`). That is the workspace-governance form.
It still can't override a device file on a laptop host.

### 3. Agent-spec `executor.auth` (per sub-agent)

The working example is `agents/rory/agents/qwen/config.yaml`:

```yaml
executor:
  type: omnigent
  model: ${CATALOG}.${SCHEMA}.qwen_code
  config: {harness: openai-agents, use_responses: false}
  auth: {type: databricks, profile: ${DBX_PROFILE}}
```

Or name a provider: `auth: {type: provider, name: fevm-codex}`. Precedence is above the family
default (`workflow.py:1181-1222`). Use this when one sub-agent must go somewhere the rest don't.

### 4. `model_egress`

It exists: `spec/parser.py:288` and `:1468-1495`, a non-empty list of HTTP egress rules such as
`POST <host>/<path>` (`inner/egress/rules.py`). **What it enforces is narrow.** It is the grant
for the *signer-backed Codex* route only (`kind: databricks` provider): the signer signs no
request outside that list, and with no list it signs only the provider's one route
(`workflow.py:358-441`, `inner/model_egress.py`). It is not a general "this harness may only call
these model endpoints" control, and it does nothing for Claude, pi, agy or openai-agents.
**OPEN: not exercised**, since it needs the `ucode` state that Codex on FEVM lacks.

### 5. Omnigent server policies

Managed Omnigent allows built-in and CEL policies only (facts row). Useful ones are
`cost_budget`, `user_daily_cost_budget`, `deny_trivial_to_expensive_model` and a CEL policy that
reads `event.context.model` and `event.context.harness`. They gate *what* a session does and
spends. They can deny a model name, but they don't choose or rewrite the endpoint, so they can't
move Codex off the org gateway. Server-side: `restrict_to_agent_names` and `OMNIGENT_SEEDED_AGENTS`
control which agents a user sees (`docs/omnigent-agents.md`).

### 6. Unity Gateway managed coding-agent config (`ug`, Beta)

`config/ug/coding-agent-config.json` (draft, see `config/ug/README.md`) is the workspace-side
control for Claude Code and Codex. It lists the model services each agent may use, their
defaults, MCP servers, skills, and `smart_routing` / `tracing` flags. Developers get it from
`ug configure`, `ug claude`, `ug codex`. Published with
`databricks api post /api/ai-gateway/v2/coding-agent-configs --profile "$DBX_PROFILE" --json @config/ug/coding-agent-config.json`.
A `GET` on that endpoint for the demo workspace returned an empty object on 2026-11-04, so
**nothing is published yet**.

This is workspace governance, but it only reaches a developer who launches through `ug` on a
workspace that publishes it. On this laptop the managed-settings `apiKeyHelper` is `ug auth-token`
and `ug`'s state decides the workspace, so **`ug configure` pointed at the FEVM workspace is the
sanctioned way to put Claude Code and Codex on FEVM** (**OPEN**: not run, because it rewrites
the shared `~/.claude` and `~/.codex` state; `ug --dry-run` prints the files without writing).

### 7. Device files (org pins win)

`managed-settings.json` (Claude) and `~/.codex/config.toml` (Codex) are the device layer. The
presenter can't override them from Omnigent, and shouldn't: that is the point of device
governance. The honest ways around them are a machine or user without those files, or `ug`
configured for the other workspace.

## (c) Where to see your traces and agent calls

| What | Where | Covers | Gaps |
| :---- | :---- | :---- | :---- |
| Sessions and transcripts | Omnigent web UI: `https://<fevm-workspace>/omnigent` (`/omnigent/c/<id>` per session) | Every Omnigent session on that server, whichever gateway the model call used | Not model-level usage |
| Per-call usage | `system.ai_gateway.usage` on the workspace (about 20 min lag, account-wide, filter `requester = current_user()`) | Calls that reached that workspace's Unity Gateway | Org-gateway Codex and Claude calls |
| Per-agent, per-session view | `just agent-calls` (`demos/routing/agent-calls.sql`) | Same table, grouped by coding agent and session | Same gaps |
| Routing view | `just dashboard-url`, then open it. `just routing-metrics` for the terminal | Talk-schema model services, route tags, fallbacks, latency | Only `*.omnigent_talk.*` services |
| Usage dashboard | **Unity Gateway > Govern > Usage Dashboard > Coding Agents** | Top sessions by spend | Same gaps |
| Gateway traces | **Govern > Traces**, backed by a Unity Catalog table | Request and response of Unity Gateway services (Beta, needs the Enhanced Unity Gateway account preview) | **Not available on the demo workspace** (facts: "No unified trace table yet") |
| MLflow traces | The unified trace table uses an "MLflow-compatible OTel schema". Omnigent itself writes none by default | Gateway and client-side coding-agent traces, if enabled | See below |

**Usage table columns** (read-only `DESCRIBE`, 2026-11-04): `request_tags map<string,string>` is
"the tags provided in the request body", and `session_metadata` is a struct of
`client_session_id`, `client_subagent_id`, `coding_agent`, `agent_version`, `surface`,
`reasoning_effort`, `smart_router_name` ("client-provided coding-agent session context").
Omnigent sends the coding-agent and surface headers (`databricks_ai_gateway.py:101-102`:
`Databricks-Custom-Coding-Agent`, `Databricks-Custom-Client-Surfaces`) and can add request tags
through `Databricks-Ai-Gateway-Request-Tags` (`:103`, CI tags from `OMNIGENT_CI_*` variables).
The org's Codex file sets its own request tags header (`source`, `org` keys). Those tags land
in the *org* table, not FEVM's.

**MLflow.** Omnigent has OpenTelemetry tracing (`inner/tracing.py`) with agent, tool and policy
spans, and its docstring names MLflow Traces as a possible backend. It is opt-in: the caller
supplies a tracer provider, and no default MLflow writer was found in the package. The gateway
side is the unified trace table above. Client-side coding-agent tracing is `"tracing":
{"enabled": true}` in the `ug` config, for Claude Code and Codex only.

**What is not visible**
- Codex calls go to the org gateway, so they don't appear in the FEVM usage table. The same goes
  for Claude (sdk and native) on this laptop.
- The org's own OpenTelemetry export (managed settings and `~/.codex/config.toml` both carry an
  `otel` block) sends prompts and tool details to the org's pipeline, not to FEVM.
- Direct pi calls on a `/serving-endpoints` surface land in `system.serving.endpoint_usage`, not
  `ai_gateway.usage`.
- Runner-log `base_url` lines show Omnigent's intent, not the destination.

**What the demo workspace's table shows today** (`just agent-calls`, 7 days): rows for
`coding_agent` values `antigravity` (surface `omnigent python-httpx`) and `Pi` (surface
`omnigent pi`), plus a Genie row. No Claude or Codex rows. That is the governance finding in one
query.

### Smart Routing on this workspace

Status: **not exercised, and not currently possible to confirm.**
- Prerequisites (docs): an *account admin* enables the Enhanced Unity Gateway preview in the
  account console, `EXECUTE` on every candidate `system.ai` model, a supported region, and
  1-2 minutes to propagate.
- Probes: `GET /api/ai-gateway/v2/coding-agent-configs` returned an empty object (no `ug`
  config, so no admin default). In 30 days of this user's usage rows, `smart_router_name` was
  non-null for 0 of 313. The account-level preview state isn't readable with a workspace
  profile (**OPEN**).
- Traffic, if the preview is on: `ug claude --enable-smart-routing` or
  `ug codex --enable-smart-routing`, or through Omnigent (0.8 or later) `omni claude
  --smart-routing --server <fevm-workspace>` or `omni codex --smart-routing --server
  <fevm-workspace>`, or pick **Smart Routing** as the harness in the UI. Give the agent a task
  that hands off to subagents: routing applies per subagent, and `--model` turns it off. Then
  check `session_metadata.smart_router_name` in `just agent-calls`.
- Caveat for this laptop: Claude Code under org-managed settings would send even Smart Routing's
  calls to the org gateway, so the proof needs `ug` configured for FEVM or another machine.
- Label it **Beta** on any slide.
