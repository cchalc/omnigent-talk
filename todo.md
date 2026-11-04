# To do

Live list of demo work still to build. The full plan is in `docs/superpowers/plans/2026-11-01-omnigent-meta-harness-talk.md`.

## Show centrally configured coding agents with `ug` (Unity Gateway CLI)

Source: https://docs.databricks.com/aws/en/ai-gateway/coding-agent-configure-govern (Beta)

Why it matters for the talk: Omnigent switches harnesses on the developer's side. Unity Gateway's managed configuration is the admin's side: one published config decides which agents, models, MCP servers and skills every developer gets, under budgets. It's the governance counterpart to the meta-harness.

Status 2026-11-03: on FEVM (`fevm-cjc`), `GET /api/ai-gateway/v2/coding-agent-configs` returns `{}` (reachable, nothing published). `ug` `0.1.0+8de04d7` is installed.

- [ ] Enable the **Unity Gateway Managed Configuration** preview on the FEVM workspace (Settings → Previews). Needs a workspace admin.
- [x] Write `config/ug/coding-agent-config.json` with no workspace IDs (public repo). Draft saved; see `config/ug/README.md` for the placeholders to replace before publishing:
  - [x] `enabled_agents` (Claude Code, Codex) and `default_agent`. Gemini CLI is not supported: the only agent enums are Claude Code and Codex
  - [x] per-agent model source via `model_services`, with `default_model`: Claude → `system.ai.claude-sonnet-5-5`, Codex → `system.ai.gpt-5-5`. Still to check: are the Opus and Haiku 5.5 services served on FEVM?
  - [ ] `mcp_servers`: one demo MCP server (placeholder `omnigent_talk.demo.<mcp-server>`)
  - [ ] `skills`: the demo skill from Task 10, so the Skills tab shows loads (placeholder `omnigent_talk.demo.gcp-databricks-facts`)
  - [x] Unity Gateway features: per-agent `smart_routing` and `tracing` enabled; `smart_defaults` deferred until the budget exists
- [ ] Publish it. UI: **Unity Gateway → Govern → Agent configuration → Edit configuration → Save**. Or CLI: `databricks api post /api/ai-gateway/v2/coding-agent-configs --profile fevm-cjc --json @config/ug/coding-agent-config.json` (update with `PATCH …/{id}?update_mask=…`).
- [ ] Grant `EXECUTE` on the chosen `system.ai.*` model services to the demo user or group.
- [ ] Set a **budget** with **Block usage** on, so `ug usage` has a limit to show.
- [ ] Developer side: `ug configure` (pulls agents and models now, and syncs MCP servers and skills), then `ug claude` / `ug codex`. Show that the defaults came from the published config.
- [ ] Show `ug usage` and `ug usage --all` (spend limits).
- [ ] Show the change propagating: edit `default_model` in the UI, run `ug configure`, relaunch, and the model is different.
- [ ] Contrast slide: **`ug` = admin-governed config per agent; Omnigent = one meta-harness across agents**. Both point at the same Unity Gateway, so usage and traces land in one place.
- [ ] Check how this interacts with `omni-fevm`: do `ug`-managed Claude/Codex settings change which gateway the Omnigent native TUIs use? Record it in `docs/omni-fevm.md`.
- [ ] Add a row to `docs/research/facts.md` for each claim used on a slide.
- [ ] Add the steps to `docs/setup-log.md` and record a fallback clip in `talk/fallbacks/`.

## Bakehouse demo (2026-11-04)

Runbook: `talk/bakehouse-demo-runbook.md`.

- [ ] Merge PRs: skills (#1) → agents (#3) → analytics (#4) and observability (#2)
- [ ] Apply `just agents-print-config` output yourself (gemini-shim provider; agy settings `model`)
- [ ] `just skills-grant <principal>` for the audience or demo group
- [ ] Govern → Traces (Beta): pick the trace table, grant `SELECT`
- [ ] Day-before: run all four agents once; open both dashboards; check dashboard/Genie lineage
- [ ] Follow-ups: cost.sql harness key for Codex/pi; skills errors show the catalog; tracebacks on network errors

## Already in flight
- [x] Round 1 harness traffic matrix: only agy (`ai_gateway.usage`) and pi (`serving.endpoint_usage`) landed on FEVM.
- [x] Fix: `databricks-fevm` is now the default for `anthropic` + `pi` in `~/.omnigent-fevm`. claude-sdk and native Claude replied on round 2.
- [x] Round 2 Claude calls missed FEVM. Cause: inherited agent-session env. Fixed with the hermetic `omni-fevm` and a host restart. Round 3 claude-sdk is confirmed on FEVM via the runner log.
- [x] Round 3 usage: claude-sdk v3 and native Claude v3 have **no FEVM rows** (likely org-managed Claude Code settings). On this laptop only agy and pi land on FEVM. See the final matrix in `docs/omni-fevm.md`.
- [ ] Optional: show Claude on FEVM from a machine or user without org-managed Claude settings, or via `ug` managed config, and confirm with a usage row.
- [ ] Demo: launch `omni-fevm` from a plain terminal, not from inside an agent session (the wrapper is hermetic now, but keep it simple).
- [ ] **Codex on FEVM:** `databricks-fevm` fails with "run `ucode configure`". Decide whether to run `ucode configure` / `ug configure` against FEVM. It rewrites the shared `~/.codex`, so it's the presenter's call. This overlaps with the `ug` section above.
- [ ] Unified trace table on FEVM (AI Gateway → Govern → Traces), so the demo doesn't depend on the 20-min usage lag.
