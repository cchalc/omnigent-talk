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
    # Hermetic: drop inherited routing vars (e.g. when launched from inside an agent session)
    set -l scrub
    for v in (set -xn | string match -r '^(?:ANTHROPIC_|CLAUDE_CODE_|OMNIGENT_|UG_).*$|^(?:CLAUDECODE|DATABRICKS_WORKSPACE_ID)$')
        set -a scrub -u $v
    end
    env $scrub \
        OMNIGENT_CONFIG_HOME=$HOME/.omnigent-fevm \
        OMNIGENT_DATA_DIR=$HOME/.omnigent-fevm \
        OMNIGENT_SERVER=https://<fevm-workspace>/api/2.0/omnigent \
        DATABRICKS_CONFIG_PROFILE=fevm-cjc \
        omni $argv
end
```

3. **Hermetic environment.** It's added because of a real bug found during testing. A shell inside an agent session (Claude Code running under another Omnigent server) exports about 60 routing variables: `ANTHROPIC_BASE_URL` from org-managed settings, plus `OMNIGENT_SERVER`, `OMNIGENT_DATABRICKS_ORG_PIN`, `OMNIGENT_CREDENTIAL_SERVICE_*` and `OMNIGENT_RUNNER_*`. A host daemon started from that shell inherited them, and claude-sdk sent its calls to the *other* workspace's gateway, even though the session lived on FEVM and the provider said `fevm-cjc`. `env -u` drops them for the child process only, so the caller's shell keeps them.

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

Two usage tables, depending on the gateway surface:
- `system.ai_gateway.usage` for Unity Gateway surfaces (`/ai-gateway/anthropic`, `/ai-gateway/mlflow`, `/ai-gateway/codex`, native Gemini). It lags about 20 min and is account-wide, so filter with `requester = current_user()`.
- `system.serving.endpoint_usage` (join `system.serving.served_entities`) for the legacy `/serving-endpoints` surface. Direct pi lands here.

**Round 1 (2026-11-03, 06:27–06:39 UTC), default providers as `omni-fevm setup` left them:**

| Harness | Lands in FEVM usage? | Where / model | Why |
|---|---|---|---|
| agy (native) | ✅ | `ai_gateway.usage`: `system.ai.gemini-3-8-flash` (client `python-httpx` = Omnigent's adapter), plus 3× `gemini-3-1-flash-lite` around agy's launch (probably agy background calls, unconfirmed) | Gemini default = `databricks-gemini-fevm-cjc` |
| pi (direct) | ✅ | `serving.endpoint_usage`: `databricks-claude-sonnet-5-5` ×2 | pi default = `databricks-fevm` |
| claude-sdk (direct) | ❌ | — | Claude default was the `claude` **subscription** (Claude CLI → org-managed settings → org gateway) |
| codex (direct) | ❌ | — | Codex default was `codex-databricks` (`~/.codex/config.toml` → org gateway) |
| claude (native TUI) | ❌ | — | same as claude-sdk |

**Fix:** in `~/.omnigent-fevm/config.yaml`, defaults are per family (`anthropic`, `openai`, `gemini`, plus an explicit `pi` scope), with at most one default per family:
```yaml
databricks-fevm: {kind: databricks, profile: fevm-cjc, default: [anthropic, pi]}
claude:          {kind: subscription, cli: claude}          # no longer default
```
**Round 2 (07:08–07:10 UTC):** claude-sdk replied `fevm-claude-sdk-v2` and native Claude Code replied `fevm-claude-native-v2`, but **neither usage table had a FEVM row**. The runner log explained it: routing chose `profile=fevm-cjc`, then `ClaudeSDKExecutor … base_url=https://<other-workspace>/ai-gateway/anthropic`. The host daemon had inherited `ANTHROPIC_BASE_URL` and about 60 `OMNIGENT_*` variables from the agent session it was started in. Fix: the hermetic wrapper above, plus `omni-fevm host stop` and a restart.

Codex on `databricks-fevm` ❌ fails with `signer-backed Codex requires configured ucode Codex state; run ucode configure`, with or without the clean environment. That command rewrites the shared `~/.codex`, so it wasn't run. Codex stays on `codex-databricks` (org gateway) for now.

**Round 3 (07:41–07:43 UTC), hermetic wrapper and restarted host:** claude-sdk replied `fevm-claude-sdk-v3` and the runner log shows `ClaudeSDKExecutor … base_url=https://<fevm-workspace>`. Native Claude Code replied `fevm-claude-native-v3`. **But neither appears in FEVM's `ai_gateway.usage` or `serving.endpoint_usage`.** No Claude rows are from the presenter or the FEVM workspace in 07:41–07:44, and the table is current to 07:49.

Likely cause (unconfirmed): both harnesses run the `claude` CLI underneath, and on this laptop the **org-managed Claude Code settings** pin `env.ANTHROPIC_BASE_URL` and `apiKeyHelper` to the org gateway with policy precedence. The CLI applies those over what Omnigent passes. So the runner-log `base_url` shows **Omnigent's intent, not where the call went**. Only a usage or trace row proves it.

### Final matrix (this laptop)

| Harness | Lands on FEVM? | Evidence |
|---|---|---|
| **agy (native Antigravity)** | ✅ | `ai_gateway.usage`: `system.ai.gemini-3-8-flash` |
| **pi (direct)** | ✅ | `serving.endpoint_usage`: `databricks-claude-sonnet-5-5` |
| claude-sdk (direct) | ❌ | no FEVM row in any round. Org-managed settings (likely) |
| claude (native TUI) | ❌ | same |
| codex | ❌ | on `codex-databricks` → `~/.codex` (org gateway). The FEVM provider needs `ucode configure` |

**Demo consequence:** the "it's all traced on *this* workspace" story uses **Antigravity + Gemini** (and pi). Claude and Codex staying on the org gateway is itself a governance point: device-level managed settings beat per-session wrappers, by design. To show Claude on FEVM, use a machine or user without those managed settings, or `ug`'s managed configuration (see `todo.md`).
