# The Omnigent ecosystem

A map of what Omnigent is and how its configuration layers fit together, from reading the
installed package (`omnigent 0.22.0.dev0`) and `--help` output on 2026-11-10. Paths in backticks
are inside the `omnigent` Python package unless they start with `docs/`. Nothing here was run
against a live server. Treat the installed source as the authority over any doc, this one included.

## Three words that get mixed up

| Term | Meaning | Where it lives |
| :---- | :---- | :---- |
| Harness | The agent loop that talks to a model and runs tools: Claude Code, Codex, pi, agy | A binary or SDK on your machine |
| Meta-harness | Omnigent: wraps harnesses and adds sessions, policies, credential and model injection, MCP bridging, agent specs | `omni` CLI, server, host daemon |
| Server | Holds sessions, history and artifacts. Local (`omni server`, SQLite) or managed on a Databricks workspace (Beta) | `127.0.0.1:6767` by default, or the workspace |

The stack is `omni -> harness -> model`. A host daemon registers the machine with a server and
spawns runners; runners tunnel back to the server over WebSocket.

## Harnesses

Registered in `harness_plugins.py`. Two modes:

- **Direct:** Omnigent drives the harness through an SDK, RPC or one CLI call per turn. Examples:
  `claude-sdk`, `codex`, `pi`, `cursor`, `antigravity`, `openai-agents`, `goose`, `qwen`, `kimi`,
  `hermes`, `copilot`.
- **Native:** the vendor's TUI runs resident in tmux and Omnigent mirrors the transcript. Names end
  in `-native` (`claude-native`, `codex-native`, `pi-native`, `antigravity-native`,
  `opencode-native`, `kiro-native`, `devin-native`, and more).

Gotchas that bite on the first day:

- `--harness claude` means `claude-sdk` (headless). `omni claude` starts `claude-native`.
- `opencode` has no headless harness, only `opencode-native`.
- There is no Gemini CLI harness. Google's `agy` is `antigravity-native`.
- A vendor ACP CLI is one data row in `acp_cli_harnesses.py`; community harnesses join through the
  `omnigent.community.harness` entry-point group.
- Per-harness binary and arguments come from, in order: CLI flag, `OMNIGENT_<NAME>_PATH`, config
  `harness.<id>.command` and `.args`, default.

## Configuration layers

Lowest precedence first (`config.py`, `_merge_effective_config`):

1. **Server config** (`omni server -c file`): database, artifacts, server-wide policies, sandbox
   provider, admins, default agent.
2. **User config** (`~/.omnigent/config.yaml`, or `$OMNIGENT_CONFIG_HOME`). `omni config set`
   accepts six keys: `default_agent`, `harness`, `model`, `opencode_model`, `server`,
   `auto_open_conversation`. Providers and auth are hand-edited.
3. **Project config** (`.omnigent/config.yaml` in the working directory). Only `harness`
   deep-merges; `model` and everything else replace.
4. **Agent spec bundle** (a directory with `config.yaml`, `spec_version: 1`): `executor` (which
   harness and model), `instructions` (falls back to `AGENTS.md`, `CLAUDE.md`, `.cursorrules`),
   `tools` (sub-agents, built-ins, MCP servers), `guardrails` (policies), `os_env`, `terminals`.
   Sub-agents sit in `agents/<name>/`, skills in `skills/<name>/SKILL.md`.

`${VAR}` expands in connection, `api_key` auth and MCP fields only. It does not expand in
`executor.model` or `auth.profile`.

This repo uses layer 4 for `agents/rory`: tracked placeholders,
rendered with real values into a gitignored copy before upload
(`agent_bundle.py`).

## Policies

Composed in `runtime/policies/builder.py` from session policies, agent guardrails and server
defaults. A DENY short-circuits, ASK accumulates for human approval, ALLOW chains. The default is
fail-closed. A spec declares one as
`guardrails.policies.<name>: {type: function, on: [...], function: {path: <dotted path>, arguments: {...}}}`,
the shape `agents/rory` uses. Other docs here write the field differently, so copy from a bundle that has run.

Built-ins (`policies/builtins/`): `cel_policy` (a CEL expression returning a result and a reason),
cost budgets, orchestration limits (`blast_radius`, `spawn_bounds`, `worktree_guard`,
`read_only_os`), and guards for GitHub and Google services. The managed Databricks server allows
built-in and CEL policies only, not custom Python (see facts.md).

Unity Gateway has its own policy layer (sensitive-data detection, MCP prompt-injection screening).
It is separate from Omnigent's.

## MCP bridging

Servers are declared in a spec as `tools.<name>: {type: mcp, command|url}`; an entry with neither
is silently skipped. Clients live in `tools/mcp.py`. The server also exposes a per-session MCP
gateway (`server/routes/mcp_gateway.py`) that checks each call against policy. Whether a harness
sees your MCP servers depends on the path: a native TUI sees what its own config declares, and a
headless harness sees only what the spec bridges.

## Sessions

Sessions have `conv_*` ids and support `--resume`, `--continue`, `--fork` and `attach`.
`omni session export` and `import` move a transcript as JSONL. Storage is SQLite with FTS5 by
default.

## Commands worth showing

| To show | Command |
| :---- | :---- |
| What is installed and chosen | `omni --version`, `omni config list`, `omni diagnose` |
| A direct harness, headless | `omni run --harness pi -p "reply OK"` |
| A native TUI | `omni claude`, `omni pi`, `omni agy` |
| An agent bundle | `omni run <dir>`, `omni agent add <dir>`, `omni agent list` |
| The host | `omni host <url>`, `omni host status`, `omni start`, `omni stop` |
| Readiness | `omni setup`, `omni login <url>` |
| Sessions | `omni session export`, `omni attach <id>` |

## Why this is the software-factory story

Each layer answers a different question, and a change at one layer does not touch the others:
which harness (project config), which model and credentials (user config and providers), what the
agent may do (spec guardrails), and who is allowed to do it (server policy). That separation is
what lets one repo carry a lean, shareable core while machine-specific detail stays out of it. See
chapter 07.

## Version drift to watch

Several installed copies can disagree: a standalone `omni` and the one bundled with a vendor
wrapper ship different versions, and older setup docs describe versions that no longer match.
Run `omni --version` from the binary you actually use. Treat a doc's line numbers as stale.
