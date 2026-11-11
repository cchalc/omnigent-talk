# 05: Smart Routing (Beta)

Tag: workspace

## Goal

Show how Unity Gateway Smart Routing picks a model and harness per task, and per subagent. Run the
preflight, preview the router's picks without running a model, run a live Claude Code session
with subagents, and read the usage rows back. Label it **Beta** on any slide.

The runbook is demos/smart-routing/README.md. The source of
claims is facts.md, section "Omnigent" and "Databricks".

Smart Routing is a different thing from the other two routing mechanisms in this repo. The demo
README keeps them apart in one table (demos/smart-routing/README.md:14-20):

| | Smart Routing (this chapter) | Custom task router (`just ask`) | Model-service traffic split |
| :---- | :---- | :---- | :---- |
| Who decides | The workspace `task_v1` router | This repo's classifier | The gateway, by fixed percentages |
| Chooses among | Claude and Codex models | Our own services (Gemini, Qwen) | Destinations of one service |

## Steps

### Requirements

These are from the docs (facts.md, "Smart Routing requirements and Omnigent steps"):

- An account admin enables the Enhanced Unity Gateway account preview. It takes 1 to 2 minutes to
  propagate.
- `EXECUTE` on every candidate `system.ai` model, in a supported region.
- Omnigent 0.8.0 or later.
- Claude Code and Codex only (facts.md, "Smart Routing behavior").
  The menus in the code cover only those two families (`src/omnigent_talk/smart_routing.py:22-25`).
  Custom model services such as `gemini_router` and `qwen_code` are not in either menu.

Smart Routing does not promise the lowest cost. The facts sheet's paraphrase of the docs says
"lowest-cost capable" (facts.md, "Smart Routing details"). The demo README
says it is "not a guarantee of lowest cost" (demos/smart-routing/README.md:27-28).
Use the README's wording. A short, well-scoped prompt can still go to the larger model
(facts.md, "Smart Routing does not minimize cost on every pick").

### A. Preflight

```bash
just smart-routing-status
```

Expected output, from demos/smart-routing/README.md:36-41:

```text
Omnigent server: smart_routing_enabled=True sources={'external': True, 'oss': True}
Unity Gateway router (task_v1): HTTP 200 -> claude-sonnet-5
```

`external` is the workspace router. `oss` is Omnigent's built-in LLM judge
(facts.md, "Omnigent server offers Smart Routing"). The recipe makes two
calls: `GET /v1/info` on the Omnigent server, and one `routes:select` on the router
(`src/omnigent_talk/cli.py:157-169`). It exits 1 when the router returns no pick.

### B. Preview the picks (no model runs on the prompts)

```bash
just smart-routing-preview
just smart-routing-preview claude
```

For each prompt in demos/smart-routing/prompts.txt and
each family, the preview asks the router for its pick and rationale (`src/omnigent_talk/cli.py:170-181`).
It does not call a model on the task itself. Each family sends its full menu, because the router
rejects a partial menu (`src/omnigent_talk/smart_routing.py:5-8`).

The menus, from `src/omnigent_talk/smart_routing.py:22-25`:

| Family | Menu |
| :---- | :---- |
| `claude` | `claude-opus-4-8`, `claude-sonnet-5` |
| `codex` | `glm-5-2`, `gpt-5-6-sol`, `gpt-5-6-luna` |

The preview makes network calls to the workspace router. The demo README calls it "offline"
(demos/smart-routing/README.md:4-5). That word is wrong for this
recipe. Treat it as workspace-tagged.

**Recorded picks** (one run, 2026-11-04, from talk/prompts.md and
facts.md, "Preview corpus outcome"):

- Short, file-referencing prompts (typo, rename, add a test) went to `claude-opus-4-8`. The
  rationale was "not_crosscutting AND not_mixed_change AND low_ambiguity all hold -> escalate".
- Trace, flaky-test, refactor and migration prompts went to `claude-sonnet-5`.
- Codex picked `gpt-5-6-sol` for every prompt.

The router runs an LLM extraction step, so a rerun can pick differently. The variance has not
been measured (facts.md, "Router picks are not guaranteed deterministic").
Say that before you run it.

### C. Live session (set up, not run yet)

> **Set up and ready, not yet run.** Everything for a live session is in place: the server offers
> Smart Routing, the router answers, and the preview picks are recorded. No live session is
> recorded in this repo. The rehearsal is pending
> (talk/prompts.md, 2026-11-04). The UI's per-subagent chips are
> UNVERIFIED on stage (facts.md, "Live subagent chips").

```bash
omni-fevm claude --smart-routing
```

`omni-fevm` is the presenter's wrapper for `omni --server <workspace>`. See
docs/omni-fevm.md. Confirm the target workspace before you run it.

Paste the stage prompt from the 2026-11-04 section of talk/prompts.md.
Watch for:

1. Three subagent rows under the session.
2. A model chip on each row, and the reason text when it shows. The docs say the reason appears
   "when available".
3. The main session's model does not change. Only subagents are routed.
4. The subagents may land on the same model. That is the router working, not failing.

Do not pass `--model`. It turns Smart Routing off, subagents included
(facts.md, "Smart Routing behavior"). The UI alternative is the
**Smart Routing** harness in the Omnigent sessions page, or Smart Routing in the Claude Code or
Codex gear menu (demos/smart-routing/README.md:86-93).

### D. Read the usage rows

```bash
just smart-routing-usage
just agent-calls
```

`smart-routing-usage` runs demos/smart-routing/usage.sql. It
selects rows where `session_metadata.smart_router_name` is set, for your user, over the last 7 days.
The column exists in the usage table (facts.md, "system.ai_gateway.usage session columns").
Rows can take up to an hour to arrive.

On the presenter's laptop, org-managed settings pin Claude Code and Codex to the org's gateway.
So the router decides, but the Claude and Codex calls most likely land in the org's usage table
(inferred, not queried), not this workspace's (demos/smart-routing/README.md:102-108;
facts.md, "Org gateway receives Claude/Codex calls"). Empty results for
Claude calls from this demo are expected, not a failure. The on-stage proof is the Omnigent UI
and the preview output.

## Verify

Offline. Checks the request body, the menus and the response parsing against a mock transport:

```bash
uv run pytest tests/test_smart_routing.py
```

The tests cover the menu per family, the prompt truncation to 4000 characters, the router call and
its error paths (`tests/test_smart_routing.py:21-74`).

Workspace. The preflight prints both lines and exits 0:

```bash
just smart-routing-status
```

### What has run, and what the repo says

| Piece | Status in the repo | Source |
| :---- | :---- | :---- |
| Preflight (server info and one router call) | Run 2026-11-04. Server reports the external and oss routers. Router answered HTTP 200 | facts.md, "Omnigent server offers Smart Routing", "Router endpoint answers" |
| Preview of seven prompts | Run once, 2026-11-04 | talk/prompts.md; facts.md, "Preview corpus outcome" |
| Live `omni-fevm claude --smart-routing` session | **Set up, not yet run** | talk/prompts.md; facts.md, "Live subagent chips" |
| Usage rows with `smart_router_name` on the demo workspace | Zero own rows in 30 days (as of 2026-11-04) | facts.md, "Smart Routing on the demo workspace" |

**Contradiction.** docs/gateway-governance.md
says, under "Smart Routing on this workspace": "Status: **not exercised, and not currently
possible to confirm.**" It also says the account-level preview state is OPEN. The facts sheet
records the preflight and the preview as run on 2026-11-04. It says the preview is "evidently on",
because the router answers (facts.md, "Omnigent server offers Smart Routing").
It also marks its own earlier OPEN row as superseded (facts.md, "Smart Routing on the demo workspace").
The governance note has not been updated. Until it is, read "not exercised" as true only for the
live session and the usage rows. The preflight and preview have run.

### Claims to avoid on stage

- That it minimizes cost on every pick.
- That the demo workspace's usage table shows this demo's Claude calls.
- That the picks are deterministic or reproducible.
- That it works with any harness other than Claude Code and Codex.
- That it replaces `just ask` or a traffic split. They solve different problems.

## Fallback

| Symptom | Action |
| :---- | :---- |
| Preflight fails, or `external` is `False` | Run step B only, and say live routing is not available today |
| No subagent chip within 60 seconds of the prompt | Stop the session. Show the `just smart-routing-preview` output, or the saved table in talk/prompts.md |
| Session does not start within 60 seconds | Same as above: step B |
| Router call returns non-200 | Step B is also down. Show the saved table and the [docs page](https://docs.databricks.com/aws/en/ai-gateway/coding-agent-model-selection) |
| Agent does not spawn subagents | Send once more: "Use the subagent tool for each task." Then fall back |
| `just smart-routing-usage` returns no rows | Expected for Claude and Codex calls on the org gateway. Not a failure |
