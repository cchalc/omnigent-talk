# 01. One prompt through each harness

Tag: workspace

## Goal

Send one tagged prompt through each harness on your managed Omnigent server, then check where each
call's traffic landed. This replays setup log sections 2 to 9, the three rounds
recorded on 2026-11-03. Your results can differ. Model names, serving, and the managed settings on
your laptop all change them. The expected results below are the ones the log recorded.

Omnigent's docs list the supported harnesses (https://omnigent.ai/docs/build/harnesses/supported)
and how to configure each one (https://omnigent.ai/docs/build/harnesses/configuration).

You need:

- Chapter 00 done, with `.env.local` holding `DBX_PROFILE`, `OMNI_SERVER`,
  `OMNIGENT_CONFIG_HOME` and `OMNIGENT_DATA_DIR`.
- The Omnigent preview turned on for the workspace (Settings, then Previews). The Sandbox preview is
  for chapter 06 (`06-policies-memory-sandbox.md`), not this one. See the
  facts row "Omnigent workspace prerequisite".
- The presenter's `omni-fevm` wrapper, described in omni-fevm. It is not in this
  repo.

Labels in the steps: **(presenter-side, not in this repo)** means the command runs through
`omni-fevm`. **(repo)** means it is a `just` recipe. **(workspace read)** means it reads the
workspace over the API and changes nothing.

`just` loads `.env.local` for recipes only. In your own shell, export `DBX_PROFILE` first, using
your profile name. Keep the value out of tracked files.

```bash
export DBX_PROFILE=<your profile name>
```

## Steps

### 1. Check the managed server (workspace read)

```bash
databricks api get /api/2.0/omnigent/v1/me --profile "$DBX_PROFILE"
```

You should get `{"is_admin": ..., "user_id": "..."}`. `Not Found` means the Omnigent preview is off
(setup log section 1). Turn it on, then run this again.

### 2. Log in and set up the isolated home (presenter-side, not in this repo)

```bash
omni-fevm login https://<workspace>
omni-fevm setup
```

- `login` reuses the OAuth grant from the Databricks CLI. No browser opens (setup log section 3).
- In `setup`, choose **Antigravity**, then **Configure native agy API key / gateway**, then
  **Databricks**, then your profile. This writes a Gemini provider named `databricks-gemini-<your
  profile>`, with `native_gemini: true` and `default: true` (setup log section 4).
- If setup says agy is "already signed in", that is agy's own Google login. A configured Gemini
  provider takes precedence over it (facts, "Native agy creds").

Give pi and the Anthropic family a Databricks provider as well. Otherwise pi borrows
`~/.codex/config.toml`, which points at a different gateway (setup log section 4). The presenter
adds defaults to the isolated config. This is the shape:

```yaml
providers:
  databricks-<name>:
    kind: databricks
    profile: <your DBX_PROFILE value>
    default: [anthropic, pi]
```

Defaults are per family, with at most one per family (omni-fevm, round 2 fix).
Setup log section 4 used `default: pi` instead. The later doc supersedes it.

Check the result:

```bash
omni-fevm config list
```

The Gemini provider should show as the default. None of your daily `~/.omnigent` providers should
appear (setup log section 2).

### 3. Register this laptop as a host (presenter-side, not in this repo)

```bash
omni-fevm host --background --no-open
omni-fevm host status
```

Expect `mode=server process=online host=online`. Stop the host with `omni-fevm host stop`. The hint
Omnigent prints says `omnigent host stop`, which targets the daily home. Don't run that one (setup
log section 5).

Start the host from a plain terminal, not from inside an agent session. A host inherits the
environment of the shell that starts it (setup log section 8, todo).

### 4. One prompt per harness (presenter-side, not in this repo)

Each prompt asks for an exact reply, so you can find the session in the web UI and in the usage
table. Use the tag `replay-<harness>-ok`. The setup log used `fevm-<harness>-ok`, so the strings
differ, but the pattern is the same.

Before you run any harness, check the shell you are in:

```bash
env | grep -E '^(ANTHROPIC_|CLAUDE_CODE_|OMNIGENT_|UG_)'
```

The wrapper scrubs these for the host it starts, but a shell inside an agent session can still send
calls to the wrong gateway. If this prints lines, start from a plain terminal (setup log section 8).

**4a. pi (direct).**

```bash
omni-fevm run --harness pi --model databricks-claude-sonnet-5-5 -p "Reply with exactly: replay-pi-ok"
```

Expect `replay-pi-ok`. Pi's call lands in `system.serving.endpoint_usage`, not in
`system.ai_gateway.usage` (see step 5). Without `--model`, pi picked a model this workspace doesn't
serve, and it returned 404. The name `system.ai.*` also returns 404 on this path, because direct
pi calls `/serving-endpoints` (setup log section 6, rows 2 to 4).

**4b. claude-sdk (direct).**

```bash
omni-fevm run --harness claude-sdk --model system.ai.claude-sonnet-5-5 -p "Reply with exactly: replay-claude-sdk-ok"
```

Expect `replay-claude-sdk-ok`. In round 3 the runner log showed the call heading to your workspace,
but no usage row appeared. The runner log shows what Omnigent asked for, not where the call went.
Only a usage row proves routing (setup log section 9). Step 5 explains why.

**4c. codex (direct).**

```bash
omni-fevm run --harness codex -p "Reply with exactly: replay-codex-ok"
```

The reply comes back. On this laptop, though, the default Codex provider reads
`~/.codex/config.toml`, which points at the organization's gateway. So this call does not land in
your workspace (setup log sections 7 and 9, omni-fevm, final matrix). Running the
same command against a workspace provider fails with a message to reconfigure Codex. That reconfigure rewrites
the shared `~/.codex`, so don't run it as part of this story. It is the presenter's call.

**4d. antigravity (the SDK harness, expected to fail).**

```bash
omni-fevm run --harness antigravity --model system.ai.gemini-3-8-flash -p "Reply with exactly: replay-antigravity-ok"
```

Expect `A Gemini API key is required` (setup log section 6, row 6). This is a teaching failure.
`antigravity` is the SDK harness, and it wants a raw Gemini key. The Databricks route only applies to
the native `omni-fevm agy` in 4f. Don't put a key in your shell to get past this error.

**4e. claude, native TUI.**

```bash
omni-fevm claude
```

In the TUI, send `Reply with exactly: replay-claude-native-ok`. Expect that reply. You will also see
the organization's Claude Code notices at launch (setup log section 6, row 10). In round 3 this
session left no usage row in your workspace, for the same reason as 4b.

**4f. agy, native TUI.**

```bash
omni-fevm agy
```

Inside agy, run `/model` and choose **Gemini 3.8 Flash**. Expect
`Model set to Gemini 3.8 Flash (Medium)`. Then send `Reply with exactly: replay-agy-ok`. Expect that
reply. The call lands in `system.ai_gateway.usage` as `system.ai.gemini-3-8-flash`, from the client
`python-httpx`, which is Omnigent's adapter (setup log section 7).

Don't pass `--model` to `omni-fevm agy`. Omnigent drops it on this path (see the gotchas below).
agy's list also shows Gemini 4 Argon. This AWS workspace doesn't serve it, so don't select it.

### 5. Check where the traffic landed (repo)

```bash
just agent-calls
```

This lists your own coding-agent calls from `system.ai_gateway.usage` over the last seven days. It
filters on `requester = current_user()`, because the table is account-wide. Expect rows for
`antigravity` (surface `omnigent python-httpx`). Pi rows appeared in a separate run (facts, 2026-11-04), not from this path. On the demo
workspace the recorded rows show no Claude or Codex traffic (facts, "Demo
workspace usage by coding agent").

Two things to know about this check:

- Usage rows take about 20 minutes to an hour to appear. If your rows are missing, wait and run it
  again. Don't read a missing row as a failed call.
- `just agent-calls` reads only `system.ai_gateway.usage`. Direct pi's calls live in
  `system.serving.endpoint_usage`, which joins to `system.serving.served_entities`. The join is in
  omni-fevm, under "Two usage tables". Run it in the workspace SQL editor.

### 6. Probe the gateway surfaces directly (workspace read)

Use these probes to show that the gateway itself works. If a harness fails and every probe returns
200, the fault is in the harness or its provider, not in the gateway (setup log section 6).

```bash
# Needs a profile logged in with `databricks auth login` (U2M). Confirm the key name on one run.
TOKEN=$(databricks auth token -p "$DBX_PROFILE" -o json | jq -r .access_token)
curl -s -o /dev/null -w '%{http_code}\n' "https://<workspace>/ai-gateway/mlflow/v1/chat/completions" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"model": "system.ai.gemini-3-8-flash", "max_tokens": 16,
       "messages": [{"role": "user", "content": "Reply with exactly: probe-ok"}]}'
```

The token stays in a shell variable. Don't echo it or write it to a file. Each surface below
returned 200 in the recorded run (setup log section 6):

| Surface path | Model | Expect |
| :---- | :---- | :---- |
| `/ai-gateway/anthropic/v1/messages` | `system.ai.claude-sonnet-5-5` | 200 |
| `/ai-gateway/mlflow/v1/chat/completions` | `system.ai.claude-sonnet-5-5`, `system.ai.gemini-3-8-flash` | 200 |
| `/serving-endpoints/chat/completions` | `databricks-claude-sonnet-5-5` | 200 |
| `/ai-gateway/codex/v1/responses` | `system.ai.gpt-5-5` | 200 |

The native Gemini route, `/ai-gateway/gemini/v1beta/models/<model>:generateContent`, is the one
agy's adapter calls (facts, "Native Gemini API route"). Chapter 02 probes it
with `just probe`.

### Per-harness gotchas

| Harness | Gotcha | Source |
| :---- | :---- | :---- |
| `--harness claude` | Means `claude-sdk` (headless). `omni claude` is the native TUI, `claude-native` | omnigent-ecosystem |
| `--harness antigravity` | The SDK harness. It needs a raw Gemini key. The Databricks route applies only to `omni-fevm agy` | setup log section 6, row 6 |
| `omni-fevm agy --model …` | On 0.22.0.dev0 the flag is dropped on the remote path (`model_override=None`), so agy uses its default, `gemini-3.1-pro-preview`, which this workspace doesn't serve. Pick the model with `/model` inside agy | setup log section 6, row 7; omni-fevm |
| agy's model list | Gemini 4 Argon is listed, but this AWS workspace doesn't serve it (Argon is not served on this workspace; see the facts sheet) | facts, FEVM row; prep reference |
| `run --harness pi` | Use a serving-endpoint name such as `databricks-claude-sonnet-5-5`. `system.ai.*` returns 404 here | setup log section 6, rows 3 and 4 |
| `run --harness claude-sdk` | `system.ai.claude-sonnet-5-5` works | omni-fevm, "Model names per harness" |
| codex | The default provider is the organization's gateway on this laptop. Routing it to a workspace needs a Codex reconfigure, which rewrites shared state | setup log section 9 |
| Claude, both harnesses | Organization-managed Claude Code settings pin the gateway, and they take precedence over Omnigent's environment (facts, "Claude managed settings beat Omnigent's env") | setup log section 9 |
| Inherited environment | A host started from a shell inside an agent session sends Claude calls to another workspace. The hermetic wrapper scrubs this | setup log section 8 |
| `just agy` | Not the same as `omni-fevm agy`. `just agy` runs bare agy through the local shim to the custom `gemini_router` service (chapter 02). It never goes through Omnigent | model services README |
| host stop | `omni-fevm host stop`, not `omnigent host stop`, which targets the daily home | setup log section 5 |
| first call after enabling the preview | May fail with `The backing service cancelled the call; please retry`. Retry | setup log section 6, row 1 |

## Verify

Each row below is one run. "Expect" is the reply the setup log recorded. "Lands" says where the
call showed up in the recorded run.

| Step | Command | Expect | Lands |
| :---- | :---- | :---- | :---- |
| 4a | `run --harness pi --model databricks-claude-sonnet-5-5` | `replay-pi-ok` | `system.serving.endpoint_usage` |
| 4b | `run --harness claude-sdk --model system.ai.claude-sonnet-5-5` | `replay-claude-sdk-ok` | Not in your workspace's usage in the recorded run |
| 4c | `run --harness codex` | `replay-codex-ok` | Organization gateway, not your workspace |
| 4d | `run --harness antigravity` | `A Gemini API key is required` (expected failure) | None |
| 4e | `omni-fevm claude` | `replay-claude-native-ok` | Not in your workspace's usage in the recorded run |
| 4f | `omni-fevm agy`, then `/model` to Gemini 3.8 Flash | `Model set to Gemini 3.8 Flash (Medium)`, then `replay-agy-ok` | `system.ai_gateway.usage`, `system.ai.gemini-3-8-flash` |

Then check these:

```bash
just agent-calls
```

It shows `antigravity` and `Pi` rows, and no Claude or Codex rows, if the usage has caught up.

```bash
omni-fevm host status
```

It shows `host=online`.

## Fallback

- **`Not Found` from `/api/2.0/omnigent/v1/me`.** The Omnigent preview is off for this workspace.
  Turn it on in Settings, then Previews, and run step 1 again.
- **404 `The given endpoint does not exist`.** The model name is wrong for this harness. Check the
  gotchas table. For pi, use `databricks-claude-sonnet-5-5`.
- **Wrapper errors.** The wrapper's own docs list these fixes (omni-fevm):
  `omni-fevm stop` for a 400, `omni-fevm login <workspace>` for a 401, and `omni-fevm setup` for a
  412.
- **No usage row after an hour.** Treat the result as unconfirmed, not failed. The runner log shows
  what Omnigent asked for. Say "intent, not confirmed" and move on. The recorded results are in the
  setup log, sections 6 to 9.
- **The gateway probes return non-200.** Check that `DBX_PROFILE` names the right profile, and that
  `databricks auth token --profile "$DBX_PROFILE"` succeeds. Until the probes pass, the gateway is
  the problem, and the harness results tell you little.
- **A harness won't start at all.** Stop the host with `omni-fevm host stop`, start it again from a
  plain terminal, and retry the step.
- **agy is stuck on a model.** Run `/model` again and choose Gemini 3.8 Flash.
- **A live run fails on stage.** Use the presenter's recorded fallback, if one exists, and say so.
  Don't claim a run that didn't happen.
