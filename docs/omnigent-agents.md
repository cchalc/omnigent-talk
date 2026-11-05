# Why the agent picker lists what it lists

The picker is not one list. It is built from three sources, and each one has a different owner
and a different way to change it. This page explains what each source is, what is in it today,
and what this repo does about it.

Code references are `omnigent/<path>:<line>` in the installed `omnigent` 0.22.0.dev0 package.
Counts and availability are the presenter's observations from the FEVM demo setup. They were not
re-read live for this page. The FEVM server runs its own build, so its roster can differ from the
package read here.

## Three sources

`sys_agent_list` fans out three reads and merges them into one result. Each source degrades to an
empty section on failure rather than failing the call.

| Source | Read from | Holds | Who can change it |
| :---- | :---- | :---- | :---- |
| `builtins` | `GET /v1/agents` | The server's roster: native harness cards, ACP CLI cards, the packaged polly and debby bundles, and any extras the operator seeds | The server operator, through env vars and seeding |
| `session_agents` | `GET /v1/sessions` | One row per session, with the agent it ran | Nothing. It is history |
| `local_configs` | `<cwd>/.omnigent/agent-configs/*.yaml` | Agent YAMLs authored in the agent's working directory | Whoever writes that file |

The merge is `omnigent/runner/tool_dispatch.py:5990` (`_agent_list_via_rest`). The three reads are
gathered at `:6039`, the projection is `:6099`, and the local scan is `_scan_local_agent_configs`
at `:5797`. The config subdirectory is set at `:638`.

Only the builtins carry availability. Each builtin row gets `available_on_host` and
`unavailable_reason` from the host's own readiness (`:6072-6080`). Readiness comes from the runner's
host identity (`_agent_list_host_readiness`, `:5954`). The same server roster can therefore look
different on two laptops.

## Built-ins

Built-ins come from three seeders that run at server startup, `_ensure_default_agents`
(`omnigent/server/app.py:1053`):

- **Native harness cards.** One `<harness>-native-ui` per native coding harness, declared in
  `omnigent/harness_plugins.py:152-263`. Seeded by `_ensure_default_native_agents` (`app.py:1224`).
  They are seeded even when the operator hides them, so old transcripts still bind to them
  (`app.py:1224` docstring).
- **ACP CLI cards.** `grok` and `jcode`, keyed by slug, not `-native-ui`
  (`omnigent/acp_cli_harnesses.py:94,112`). Seeded by `_ensure_default_acp_agents` (`app.py:1315`).
- **Packaged bundles.** `debby` and `polly`, seeded by `_ensure_default_debby_agent` (`app.py:1424`)
  and `_ensure_default_polly_agent` (`app.py:1492`) from `omnigent/resources/examples/`.
- **Extras.** `OMNIGENT_BUILTIN_AGENT_DIRS` (`app.py:1124`) takes an `os.pathsep` list of spec files
  or bundle directories. The name is the file stem or directory name. A bad entry is logged and
  skipped. Extras are never filtered by the allowlist below.

The operator's filter is `OMNIGENT_SEEDED_AGENTS` (`omnigent/server/seeded_agents.py:20`). Unset
means every packaged built-in is offered. Set to a list means only those. Set to empty means none.
A suppressed row is hidden from `GET /v1/agents`, not deleted (`app.py:1053` docstring).

### Availability rules

`omnigent/harness_availability.py:36-53` maps a readiness value to the picker's answer:

- `True` means available.
- `False`, or no entry at all, means `unavailable_reason: "unconfigured"`.
- A string gives its own reason: `binary-missing`, `version-too-low`, or `needs-auth`.
- `needs-auth` is advisory. `harness_launch_availability` (`:56`) returns `available_on_host: null`,
  because a session can bring its own credentials.

The readiness map is `configured_harness_map` (`omnigent/onboarding/harness_readiness.py:1035`).
CLI-backed harnesses report `binary-missing`, `version-too-low`, or `needs-auth` from
`_cli_family_availability` (`:917`).

### Inventory

Availability is as observed on the presenter's host. The "why" column is the rule that applies, not
a fresh probe.

| Built-in | Harness | Available today | Why |
| :---- | :---- | :---- | :---- |
| debby | `claude-sdk`, with `claude` and `gpt` sub-agents | yes | Packaged bundle. Needs a Claude and an OpenAI provider |
| polly | `claude-sdk`, with seven sub-agents | yes | Packaged bundle. Needs a Claude provider |
| claude-native-ui | `claude-native` | yes | CLI installed and signed in or provider configured |
| codex-native-ui | `codex-native` | yes | Codex auth readiness passes |
| cursor-native-ui | `cursor-native` | yes | CLI installed and signed in |
| pi-native-ui | `pi-native` | yes | Binary present with a provider or subscription |
| antigravity-native-ui | `antigravity-native` | yes | Antigravity credential present |
| grok | ACP CLI `grok` | no | Not ready on this host (`unconfigured`). ACP rows gate on the binary |
| jcode | ACP CLI `jcode` | no | Not ready on this host (`unconfigured`). ACP rows gate on the binary |
| kiro-native-ui | `kiro-native` | no | Not ready on this host (`unconfigured`) |
| kimi-native-ui | `kimi-native` | no | Not ready on this host (`unconfigured`) |
| goose-native-ui | `goose-native` | no | Not ready on this host (`unconfigured`) |
| hermes-native-ui | `hermes-native` | no | Not ready on this host (`unconfigured`) |
| qwen-native-ui | `qwen-native` | no | Not ready on this host (`unconfigured`) |
| devin-native-ui | `devin-native` | no | Not ready on this host (`unconfigured`) |
| opencode-native-ui | `opencode-native` | no | `version-too-low`: CLI present but too old (`harness_readiness.py:902`) |

For a native row, `unconfigured` alone does not say whether the CLI is missing or unsigned. The
per-row `unavailable_reason` is the place to look.

## Session agents

Session rows are not curated. Every past session adds one, so the list grows with use. The count
the presenter saw today was 23 rows, which collapse to about ten distinct agents.

| Group | Names (as listed) | Where they came from | Decision |
| :---- | :---- | :---- | :---- |
| Native cards | `claude-native-ui` (several), `codex-native-ui`, `antigravity-native-ui` | Normal use in the talk build | Keep. This is the real history |
| SDK smoke probes | `codex`, `claude-sdk`, `pi`, `antigravity` | FEVM per-harness probes, each replying `fevm-<harness>-ok` (`docs/setup-log.md`, around lines 83-95) | Document only. Some failed and their runners are offline |

The smoke-probe rows are evidence for the setup log, so they stay. Closing them would change the
history the talk points to. Failed rows with offline runners are unlikely to launch, and the
list does not hide them.

## How polly and debby are built

A bundle is a directory. `omnigent/spec/parser.py:202` (`parse`) reads it:

- `config.yaml` is the agent: `spec_version`, `name`, `description`, `executor`, `prompt`,
  `tools.agents`, `os_env`, and `guardrails.policies`.
- `agents/<dir>/config.yaml` are sub-agents, discovered recursively by `_discover_sub_agents`
  (`parser.py:3324`). Each pins its own harness.
- `skills/<name>/SKILL.md` are skills, discovered by `_discover_skills` (`parser.py:2502`).

Both bundles put the brain on `claude-sdk` with `smart_routing_harness: auto`. The comments say why:
pinning the brain pins the family its workers route within, which strands the codex and pi
sub-agents (`polly/config.yaml:33-35`).

**debby** (`resources/examples/debby/`): fan out each question to two responders.

| Sub-agent | Harness | Role |
| :---- | :---- | :---- |
| `claude` | `claude-sdk` | Claude responder. Answers, then critiques in debate mode |
| `gpt` | `codex` | GPT responder. Answers, then critiques in debate mode |

Debby has one skill, `debate`, which runs a critique loop for N rounds before a synthesis. Her
`gpt` head is on `codex` on purpose. The `openai-agents` harness would fall back to ambient
Databricks credentials for an unpinned model (`debby/agents/gpt/config.yaml`, header comment).

**polly** (`resources/examples/polly/`): a coding orchestrator. It writes no code itself.

| Sub-agent | Harness | Role |
| :---- | :---- | :---- |
| `claude_code` | `claude-native` | Implements, cross-reviews, or explores in its own terminal |
| `codex` | `codex-native` | Same role, Codex CLI |
| `opencode` | `opencode-native` | Same role, OpenCode server |
| `cursor` | `cursor-native` | Same role. Model pinned to `grok-4.5` |
| `hermes` | `hermes-native` | Same role, Hermes Agent |
| `agy` | `antigravity-native` | Same role, Gemini-native Antigravity CLI |
| `pi` | `pi` | Headless. Review and explore, on any gateway model per dispatch |

Polly has three skills: `fanout`, `cross-review`, and `investigate`. Its guardrails are
`blast_radius` (catastrophic git and shell actions denied), `spawn_bounds` (at most six dispatches
per turn, counting `sys_session_create`), and `headless_subagent_purpose_guard` (only implement,
review, explore, or search purposes). `spawn: true` lets it define its own children.

## Making your own agent appear

There are three routes. They do different things, so pick by what you want to show.

1. **Local config. Visible to agents only.** Write a top-level YAML at
   `<cwd>/.omnigent/agent-configs/<name>.yaml`. Subdirectories are not scanned, and bundles are not
   read from this path. It appears in `local_configs` with its name, path, and description. It does
   not appear in the New Chat picker. Launch it with the `config_path` route below.

2. **`sys_session_create(config_path=…)`. Launches, adds no card.** An agent passes a YAML, a
   directory, or a tarball inside its working directory. The runner uploads it and starts a child
   session from it (`omnigent/runner/tool_dispatch.py:3466`; `_upload_config_bundle` at `:3789`
   posts to `/v1/sessions` at `:3838`, with the parent forced). This creates a session. I did not
   trace whether the upload also stores an agent row.

3. **`omnigent agent add <dir>`. Adds a card for the account.** The CLI installs the agent as a user
   agent (`omnigent/cli.py:12483`, posting to `/v1/agents` at `:12468`). Re-adding replaces it. The
   CLI help says it then appears beside the built-ins. The server confirms the split: the
   unscoped `GET /v1/agents` never returns user agents
   (`omnigent/server/routes/builtin_agents.py:452`).
   User agents are listed with `GET /v1/agents?scope=user`. So they are not in the `builtins`
   section of `sys_agent_list`. How the web picker shows them is not verified here.

A local config is for agents to find and launch. A card in the picker needs `omnigent agent add`.

## Curation decisions

- **Keep the packaged roster.** Polly and debby are the two orchestrator stories for the talk.
- **Keep the unavailable native cards.** They are seeded so old transcripts still bind. Removing
  them takes `OMNIGENT_SEEDED_AGENTS`, which is a server-wide setting. It is not this repo's to set.
- **Trim the New Chat picker for the stage with `restrict_to_agent_names`, not a suppression.** It
  is display-only and reads from the server config (`omnigent/server/server_config.py:56,177`).
  `default_agent_name` picks the starting card. A user's remembered pick still wins. The presenter
  applies it to the server config. This repo does not write it.
- **Do not close the smoke-probe sessions.** Document them and leave them. They are the record
  behind `docs/setup-log.md`.
- **Do not add a local config to make an agent appear in the picker.** It will not. Use
  `omnigent agent add`.
- **Do not edit the Omnigent homes.** Recipes print config for the presenter to apply.

## Custom agent: `rory`

`agents/rory/` is this repo's own bundle. Polly and debby split work by vendor. Rory splits it
by task: review and deploys go to Codex, and SQL and simple one-shot answers go to the logical
qwen worker on the talk schema's own 50/50 Qwen/Gemini model service.

| Part | Harness | Role |
| :---- | :---- | :---- |
| `rory` (router) | `claude-sdk` | Classifies the request, dispatches it, and starts each reply with `route: <task> -> <worker>`. Writes no code. `approval_relay` (CEL: ASK before any message containing `APPROVED`), `spawn_bounds` of 3 per turn |
| `codex` | `codex` (headless) | `REVIEW:` reads the diff and lists findings. `PLAN:` runs `just gateway-validate` and `just gateway-plan`. Deploys only on `DEPLOY APPROVED` |
| `qwen` | `openai-agents` | No tools. Model `${CATALOG}.${SCHEMA}.code_router` over the gateway's chat completions (`use_responses: false`), with Databricks profile auth from `DBX_PROFILE`; the service routes 50/50 between Qwen and Gemini, with a fallback |

Skills: `review` (how to brief codex) and `deploy` (the two-phase gate). The workers are
headless and cannot answer an approval prompt, so the approval happens in rory's conversation
with the user. Rory relays `DEPLOY APPROVED` only after the user says yes. The `approval_relay`
policy also stops any `sys_session_send` that contains `APPROVED` with an ASK, so a model slip
cannot skip the human. `blast_radius` would not catch it: it asks only for kubectl, helm,
terraform or databricks commands (`omnigent/policies/builtins/orchestration.py:74-77`), and
`just gateway-deploy` matches none of them.

**Registering.** `omnigent agent add` expands `${VAR}` only in connection, api_key auth and MCP
fields (`omnigent/cli.py:6525`), not in `executor.model` or `auth.profile`. The tracked bundle
therefore keeps placeholders. `just agent-render` fills them from `.env.local` into the
gitignored `.omnigent/rory/`, and `just agent-add` renders and uploads that copy.
`just agents` lists it.

**Where it shows up.** As the code predicts, after `just agent-add` rory is in
`omnigent agent list` (user scope) and launches by agent id with `sys_session_create`. It is
not in the `builtins` section of `sys_agent_list`, which reads the unscoped `GET /v1/agents`.

**Verified 2026-11-03** on the FEVM server:
- The code service now named `code_router` was deployed (`just gateway-deploy`).
- A spike of the qwen worker returned SQL.
- A rory session routed the SQL demo prompt to `qwen` and the review prompt to `codex`.

The prompts and outcomes are in `talk/prompts.md`.
