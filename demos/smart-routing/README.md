# Smart Routing (Beta)

**Label this Beta on the slide.** Unity Gateway Smart Routing picks a model (and, in Omnigent,
a harness) per task, and per subagent. This runbook shows the router's decisions two ways:
offline with `just smart-routing-preview`, and live in an Omnigent session on the FEVM
workspace.

Source: https://docs.databricks.com/aws/en/ai-gateway/coding-agent-model-selection (facts in
`docs/research/facts.md`, Omnigent section). Placeholders: `<fevm-workspace>` is the demo
workspace URL; it lives only in `.env.local` and the `omni-fevm` wrapper.

## Three things that get confused

| | Smart Routing (this demo) | Custom task router (`just ask`) | Model-service traffic split |
| :---- | :---- | :---- | :---- |
| Who decides | Unity Gateway's `task_v1` router (or Omnigent's built-in LLM judge) | This repo's classifier (`router.py`) | The gateway, by fixed percentages |
| Chooses among | Claude and Codex models in `system.ai` (and the harness, in Omnigent) | Our own model services (Gemini, Qwen) | Destinations of one model service |
| Input | The task text, per subagent | The prompt, once | None; random by weight |
| Config | Admin preview plus `--smart-routing` | `just ask` | `resources/` bundle |
| Where it shows | Omnigent UI chip, `smart_router_name` in usage | `just routing-metrics` | `just gateway-show` |

## Requirements (all from the docs)

- Enhanced Unity Gateway account preview enabled by an account admin (1-2 minutes to propagate).
- `EXECUTE` on every candidate `system.ai` model; a supported region.
- Omnigent 0.8.0 or later. Works with Claude Code and Codex only.
- Not a guarantee of lowest cost: the docs describe it as picking by complexity, permissions
  and budget.

## Preflight (5 minutes before)

```bash
just smart-routing-status
```

Expected:

```
Omnigent server: smart_routing_enabled=True sources={'external': True, 'oss': True}
Unity Gateway router (task_v1): HTTP 200 -> claude-sonnet-5
```

`external` is the workspace router, `oss` is Omnigent's built-in LLM judge. If either line
differs, use the fallback section. Also: `omni-fevm host status` shows `host=online`.

## Segment script (about 8 minutes)

### A. The router's picks, offline (2 min)

```bash
just smart-routing-preview
```

Point at: the same router call Omnigent makes, run without a model on the prompts. Short,
well-scoped prompts that name a file ("Rename `cnt` to `count` in src/...") escalated to
`claude-opus-4-8`: the rationale reads `not_crosscutting AND not_mixed_change AND
low_ambiguity all hold -> escalate`. The error-trace, flaky-test and cross-cutting prompts
stayed on the default `claude-sonnet-5`. Codex picked `gpt-5-6-sol` for every prompt. The router
uses an LLM extraction step, so picks are not deterministic: your run may differ from
the table in `talk/prompts.md`. Say so before running it.

### B. Live, Claude Code with `--smart-routing` (3 min)

```bash
omni-fevm claude --smart-routing
```

(`omni-fevm` is the presenter's fish wrapper for `omni --server <fevm-workspace>`; see
`docs/omni-fevm.md`.) Paste the stage prompt:

> Use three subagents, one per task, and run them in parallel. Change no files. (1) In
> README.md, say in one sentence what this repo is for. (2) Explain what `parse_label` in
> src/omnigent_talk/router.py does and what it returns for an empty answer. (3) Review how
> gateway.py, router.py and routing.py handle 429s and retries across the whole package, and
> list the three riskiest gaps. When all three finish, tell me which model each subagent used.

What to point at in the UI:

1. Three subagent rows appear under the session.
2. The model chip on each row, and the rationale text when shown. The docs say the agent shows
   each subagent's selected model and, when available, the reason.
3. The main session's own model does not change. Only subagents are routed.
4. The subagents do not all need to land on different models. Say that if they do not; that is
   the router working, not failing.

### C. Same thing through the UI harness (2 min)

Open the sessions page at `<fevm-workspace>/omnigent`, start a new session, pick **Smart
Routing** as the harness (it chooses harness and model), and paste the same stage prompt.
Alternative: pick Claude Code or Codex and choose Smart Routing in its gear menu. Point at the
harness and model the router chose for the session.

Do not pass `--model`: it turns Smart Routing off, including for subagents.

## Verification, and a caveat stated plainly

```bash
just smart-routing-usage   # rows with smart_router_name in this workspace's usage table
just agent-calls           # per coding agent, per session
```

**Caveat.** On the presenter's laptop, org-managed settings pin Claude Code (and Codex) to the
org's Unity Gateway. FEVM's router decides, but Claude and Codex inference runs on the org
gateway, so those usage rows, and the `smart_router_name` value, land in the org's table, not
FEVM's. Expect `just smart-routing-usage` and `just agent-calls` on FEVM to show no Claude
calls from this demo. They can be empty, and that is not a failure. On-stage proof of the
decision is the Omnigent UI (model chip and rationale per subagent) plus the preview output.
Rows can also take up to an hour to arrive.

## Fallback

| Symptom | Action |
| :---- | :---- |
| Preflight fails, or `external` is False | Run segment A only; say live routing is not available today |
| No subagent chip within 60 seconds of the prompt | Stop the session; switch to `just smart-routing-preview` output (or the saved copy in `talk/prompts.md`) |
| Session does not start within 60 seconds | Same: segment A |
| Router call returns non-200 | Segment A is also down; show the saved table in `talk/prompts.md` and the docs page |
| Agent does not spawn subagents | Re-send once: "Use the subagent tool for each task." Then fallback |

## Say / don't say

Say:
- "Smart Routing is Beta."
- "Each subagent is routed independently; the main session stays on its default model."
- "The router showed its rationale. Picks can vary between runs."
- "The decision is made by FEVM's gateway; on this laptop the model call itself goes through
  our org gateway."

Don't say:
- That it minimizes cost on every pick. Short, well-scoped tasks escalated to the larger
  model in the probe.
- That FEVM's usage table shows the Claude calls from this demo.
- That picks are deterministic or reproducible.
- That it works with other harnesses than Claude Code and Codex.
- That it replaces `just ask` or a traffic split. They solve different problems (table above).
