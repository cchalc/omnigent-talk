# Setup log: Omnigent on the FEVM workspace

A step-by-step record of standing up the demo environment, written to be replayed on stage. Each entry has the command, what happened, and what we learned. Failures are kept on purpose, because they're the harness-engineering story.

Public repo: the workspace host is written as `<fevm-workspace>` and IDs are omitted. Times are UTC.

---

## 2026-11-03 · Session 1: from "no traces in logfood" to four harnesses on one workspace

### 0. Why a dedicated workspace
- Gateway traces weren't reachable from the shared internal workspace: no `BROWSE` on the `system` catalog, and no `unity_gateway_otel_spans` table.
- Picked an FEVM workspace where the presenter is a **workspace admin** (Databricks profile `fevm-cjc`, AWS `us-east-1`).
- Probe: on FEVM, `system.ai_gateway.usage` *is* readable. **Databricks point:** usage and traces are Unity Catalog tables, governed like any other data.

### 1. Is there a managed Omnigent server on the workspace?
```bash
databricks api get /api/2.0/omnigent/v1/me --profile fevm-cjc
# → Error: Not Found
```
- Same probe on a workspace with Omnigent enabled returns `{"user_id": …}`. This is the same probe `omni login` uses.
- **Fix:** FEVM workspace → **Settings → Previews** → enable **Omnigent** (and **Databricks Sandbox**). Then:
```bash
databricks api get /api/2.0/omnigent/v1/me --profile fevm-cjc
# → {"is_admin": true, "user_id": "<me>"}
```
- **Databricks point:** the Omnigent server is a workspace feature. It needs no infra and uses workspace SSO, and the presenter is admin of their own server.

### 2. A wrapper per workspace: `omni-fevm`
The presenter already had `omni-dev` / `omni-gtm` (`isaac omni` with a server override). `omni-fevm` is different on purpose (see `docs/omni-fevm.md`):
```fish
function omni-fevm
    set -lx OMNIGENT_CONFIG_HOME $HOME/.omnigent-fevm   # isolated config
    set -lx OMNIGENT_DATA_DIR    $HOME/.omnigent-fevm   # isolated tokens, host daemon, logs
    set -lx OMNIGENT_SERVER      https://<fevm-workspace>/api/2.0/omnigent
    set -lx DATABRICKS_CONFIG_PROFILE fevm-cjc
    omni $argv
end
```
- Lives in home-manager (nix), so it's applied with `home-manager switch --flake .`.
- Check: `omni-fevm config list` shows **none** of the daily `~/.omnigent` providers. The daily config is untouched.

### 3. Log in (no browser needed)
```bash
omni-fevm login https://<fevm-workspace>
# Using https://<fevm-workspace>/omnigent (Databricks workspace-hosted omnigent).
# … authenticates via the Databricks workspace https://<fevm-workspace>.
# Set https://<fevm-workspace>/omnigent?o=… as your default server.
```
- It reused the existing `fevm-cjc` OAuth grant from the Databricks CLI. One identity covers CLI, gateway and Omnigent.
- Check: daily `~/.omnigent/config.yaml` still points at the old server. Only `~/.omnigent-fevm` changed.

### 4. `omni-fevm setup`: Antigravity on Databricks Gemini
- Setup said agy was **already signed in**. That's agy's own Google login in the macOS Keychain.
- That's fine. Omnigent prefers a configured provider over agy's login: (1) the default Gemini provider, (2) a Gemini API key, (3) only then agy's own sign-in.
- Chose **Antigravity → Configure native agy API key / gateway → Databricks → profile `fevm-cjc`**, which wrote:
```yaml
providers:
  databricks-gemini-fevm-cjc:
    kind: databricks
    profile: fevm-cjc
    native_gemini: true     # agy keeps speaking the native Gemini API, routed via Unity AI Gateway
    default: true
```
- pi was still borrowing Codex's gateway config (`~/.codex/config.toml` → a *different* workspace). Added a pi default for FEVM:
```yaml
  databricks-fevm:
    kind: databricks
    profile: fevm-cjc
    default: pi
```

### 5. Register this laptop as a host
```bash
omni-fevm host --background --no-open
omni-fevm host status
#   mode=server  process=online  host=online
```
- The daily hosts for the other two servers kept running side by side. Omnigent keeps one host daemon per server.
- Gotcha: the hint prints `omnigent host stop`. For this setup use **`omni-fevm host stop`**, or you'll stop the wrong one.

### 6. One prompt per harness
Each run gets a tagged prompt (`Reply with exactly: fevm-<harness>-ok`), and each creates a session at `https://<fevm-workspace>/omnigent/c/<id>`.

| # | Command | Result | Lesson |
|---|---|---|---|
| 1 | `omni-fevm run --harness pi -p …` | ❌ `The backing service cancelled the call; please retry` | first call right after enabling the preview; retry worked |
| 2 | same | ❌ `404 The given endpoint does not exist` | pi picked a default model FEVM doesn't serve |
| 3 | `… --harness pi --model system.ai.claude-sonnet-5-5` | ❌ same 404 | **direct pi on a `kind: databricks` provider calls `/serving-endpoints`, where `system.ai.*` names don't exist** |
| 4 | `… --harness pi --model databricks-claude-sonnet-5-5` | ✅ `fevm-pi-ok` | use the serving-endpoint name for direct pi |
| 5 | `… --harness claude-sdk --model system.ai.claude-sonnet-5-5` | ✅ `fevm-claude-sdk-ok` | Omnigent drives Claude itself via the Anthropic gateway surface |
| 6 | `… --harness antigravity --model system.ai.gemini-3-8-flash` | ❌ `A Gemini API key is required` | `antigravity` is the **SDK** harness. The Databricks route is for the **native** `omni agy` |
| 7 | `omni-fevm agy --model gemini-3.8-flash-medium` | ❌ `Databricks does not expose an unambiguous Gemini model for 'gemini-3.1-pro-preview'` | the request reached Omnigent's Databricks adapter (good), but `--model` was dropped on the remote path (`model_override=None`), so agy used its default |
| 8 | in agy: `/model` → **Gemini 3.8 Flash** | ✅ `Model set to Gemini 3.8 Flash (Medium)` → `fevm-agy-ok` | switch the model inside agy. agy's own list also offers **Gemini 4 Argon**, which this AWS workspace doesn't serve (GCP-only) |
| 9 | `omni-fevm run --harness codex -p …` | ✅ `fevm-codex-ok` | |
| 10 | `omni-fevm claude` (native TUI) | launched; shows the org (Isaac) notices | org-managed Claude Code settings are in force |

Direct gateway check, so the failures above weren't the gateway's fault. Every FEVM surface returned **200** (curl with the `fevm-cjc` token):

| Surface | Model | HTTP |
|---|---|---|
| `/ai-gateway/anthropic/v1/messages` | `system.ai.claude-sonnet-5-5` | 200 |
| `/ai-gateway/mlflow/v1/chat/completions` | `system.ai.claude-sonnet-5-5` | 200 |
| `/ai-gateway/mlflow/v1/chat/completions` | `system.ai.gemini-3-8-flash` | 200 |
| `/serving-endpoints/chat/completions` | `databricks-claude-sonnet-5-5` | 200 |
| `/ai-gateway/codex/v1/responses` | `system.ai.gpt-5-5` | 200 |

**Databricks point:** one workspace serves Claude, Gemini and GPT behind one identity, in four API dialects (Anthropic, OpenAI chat, OpenAI Responses, native Gemini). Every harness speaks its own dialect, and none of them needs a vendor API key.

### 7. Where did the traffic land? (`system.ai_gateway.usage`)
See the matrix in `docs/omni-fevm.md` (filled in from the query there).

---

## Replay script for the demo
1. `databricks api get /api/2.0/omnigent/v1/me --profile fevm-cjc` shows the managed server exists.
2. `type omni-fevm` shows the wrapper is just environment variables plus `omni`.
3. `omni-fevm config list` shows the Gemini provider `databricks-gemini-fevm-cjc ✓ default`.
4. `omni-fevm agy`, then `/model` → Gemini 3.8 Flash, then a prompt. Native Antigravity runs on Databricks Gemini.
5. In the same session, open `https://<fevm-workspace>/omnigent` in the browser or Android app.
6. Run the usage query on FEVM and point at the agy row.
