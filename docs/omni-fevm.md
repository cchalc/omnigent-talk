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
2. `omni-fevm login https://<fevm-workspace>`. It reuses the Databricks CLI's `fevm-cjc` OAuth grant, so no browser is needed.
3. `omni-fevm setup` → **Antigravity → Configure native agy API key / gateway → Databricks → `fevm-cjc`**. This writes provider `databricks-gemini-fevm-cjc` with `native_gemini: true`. If setup says agy is "already signed in", that's agy's own Google login, which is fine: a configured Gemini provider takes precedence over it.
4. Give pi a FEVM provider. Otherwise it borrows Codex's `~/.codex/config.toml`, which points at another workspace:
   ```yaml
   databricks-fevm: {kind: databricks, profile: fevm-cjc, default: pi}
   ```
5. `omni-fevm host --background --no-open`, then `omni-fevm host status` (expect `host=online`). Stop it with **`omni-fevm host stop`**. The printed hint `omnigent host stop` targets the daily home instead.

If something fails: `omni-fevm stop` (400), then `omni-fevm login <ws>` (401), then `omni-fevm setup` (412).

### Model names per harness (the gotchas)
- **agy (native):** pick the model *inside* agy: `/model` → **Gemini 3.8 Flash**. On omnigent `0.22.0.dev0`, `omni agy --model …` is dropped on the remote-server path (`model_override=None`), and agy's default `gemini-3.1-pro-preview` isn't served by FEVM. agy's list also shows **Gemini 4 Argon**, which this AWS workspace doesn't serve (Argon is GCP-only).
- **pi (direct `run --harness pi`):** use the serving-endpoint name **`databricks-claude-sonnet-5-5`**. Direct pi on a `kind: databricks` provider calls `/serving-endpoints`, where `system.ai.*` names return 404.
- **claude-sdk (direct):** `system.ai.claude-sonnet-5-5` works (Anthropic gateway surface).
- **`--harness antigravity`** is the Antigravity *SDK* harness and wants a raw `GEMINI_API_KEY`. The Databricks route only applies to native `omni agy`.

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
