# `omni-fevm`: one Omnigent per demo workspace

The talk demos run against one Databricks workspace (an AWS FEVM workspace, Databricks profile `fevm-cjc`). The presenter's daily Omnigent setup stays untouched. This page shows how, and why it's built this way. It doubles as the source for the "harness engineering" slide.

> Public repo: the real workspace host lives only in the presenter's shell function and `.env.local`. Below it's `<fevm-workspace>`.

## The wrapper

The presenter already had two wrappers that pin `isaac omni` to a managed Omnigent server:

```fish
omni-gtm  →  ISAAC_OMNI_SERVER=https://<gtm-workspace>/api/2.0/omnigent isaac omni $argv
omni-dev  →  ISAAC_OMNI_SERVER=https://<devtools-workspace>/api/2.0/omnigent isaac omni $argv
```

`omni-fevm` follows the same idea, with two deliberate differences. It's defined in home-manager (`modules/home-manager/fish/default.nix` in the presenter's nix-config):

```fish
function omni-fevm --description 'plain omni on the FEVM demo workspace (fevm-cjc, ~/.omnigent-fevm)'
    set -lx OMNIGENT_CONFIG_HOME $HOME/.omnigent-fevm
    set -lx OMNIGENT_DATA_DIR $HOME/.omnigent-fevm
    set -lx OMNIGENT_SERVER https://<fevm-workspace>/api/2.0/omnigent
    set -lx DATABRICKS_CONFIG_PROFILE fevm-cjc
    omni $argv
end
```

1. **Plain `omni`, not `isaac omni`.** Isaac is internal Databricks tooling. It pre-configures Claude Code and Codex against its own gateway workspace. Changing only the *server* would leave model calls, and so usage and traces, in the wrong workspace.
2. **Isolated state.** `OMNIGENT_CONFIG_HOME` and `OMNIGENT_DATA_DIR` move the whole Omnigent home: `config.yaml`, `auth_tokens.json`, the host daemon, and logs. Nothing in `~/.omnigent` is read or written, so demo setup can't break the daily-use config.

Demo scripts in this repo get the same isolation by sourcing `.env.local`, which sets `OMNIGENT_CONFIG_HOME`, `OMNIGENT_DATA_DIR`, and `OMNI_SERVER`.

## Two layers: server vs. gateway

| Layer | What it owns | Set by |
|---|---|---|
| **Omnigent server** | sessions, web UI, sharing/collaboration, mobile app, policies | `OMNIGENT_SERVER` / `--server` |
| **Model gateway** | which workspace's Unity AI Gateway serves the model, which is where **usage and traces** land | the harness's provider config |

Normally Omnigent sets the second layer from its provider (`omni-fevm setup` → *Databricks — workspace* → `fevm-cjc`). But a harness can carry its own pinned gateway config, which wins. On the presenter's laptop, org-managed Claude Code settings and `~/.codex/config.toml` pin the org gateway. That's device-level governance working as designed, and it's worth showing.

## First-time setup

1. In the FEVM workspace, go to **Settings → Previews** and enable **Omnigent** (and **Databricks Sandbox** for the sandbox demo).
   Check: `databricks api get /api/2.0/omnigent/v1/me --profile fevm-cjc` returns your user, not `Not Found`.
2. `omni-fevm setup`: choose *Databricks — workspace* → `fevm-cjc`, and enable pi, agy, claude, and codex. For Antigravity, choose *Configure native agy API key / gateway* → Databricks profile (writes `native_gemini: true`) and use model `system.ai.gemini-3-8-flash`.
3. `omni-fevm login https://<fevm-workspace>` (browser), then `omni-fevm host`, then `omni-fevm diagnose`.

If something fails: `omni-fevm stop` (400), then `omni-fevm login <ws>` (401), then `omni-fevm setup` (412).

## Where does each harness's traffic land?

Send one tagged prompt per harness (`omni-fevm pi`, `omni-fevm agy`, `omni-fevm claude`, `omni-fevm codex`), then on FEVM run:

```sql
SELECT event_time, endpoint_name, destination_model,
       session_metadata.coding_agent, session_metadata.surface, requester
FROM system.ai_gateway.usage
WHERE event_time > now() - INTERVAL 1 HOUR
ORDER BY event_time DESC;
```

| Harness | Shows up in FEVM usage? | Model | Notes |
|---|---|---|---|
| pi | _pending_ | | Omnigent provider |
| agy (Antigravity) | _pending_ | `system.ai.gemini-3-8-flash` | native Gemini route |
| claude (native TUI) | _pending, expected no_ | | org-managed settings pin the gateway |
| codex (native TUI) | _pending, expected no_ | | `~/.codex/config.toml` pins the gateway |
| claude-sdk (direct) | _pending_ | | Omnigent drives the model itself |
