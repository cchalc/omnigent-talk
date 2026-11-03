# To do

Live list of demo work still to build. The full plan is in `docs/superpowers/plans/2026-11-01-omnigent-meta-harness-talk.md`.

## Show centrally configured coding agents with `ug` (Unity Gateway CLI)

Source: https://docs.databricks.com/aws/en/ai-gateway/coding-agent-configure-govern (Beta)

Why it matters for the talk: Omnigent switches harnesses on the developer's side. Unity Gateway's managed configuration is the admin's side: one published config decides which agents, models, MCP servers and skills every developer gets, under budgets. It's the governance counterpart to the meta-harness.

Status 2026-11-03: on FEVM (`fevm-cjc`), `GET /api/ai-gateway/v2/coding-agent-configs` returns `{}` (reachable, nothing published). `ug` `0.1.0+8de04d7` is installed.

- [ ] Enable the **Unity Gateway Managed Configuration** preview on the FEVM workspace (Settings → Previews). Needs a workspace admin.
- [ ] Write `config/ug/coding-agent-config.json` with no workspace IDs (public repo):
  - [ ] `enabled_agents` (Claude Code, Codex, plus Gemini CLI if supported) and `default_agent`
  - [ ] per-agent model source via `model_services`, with `default_model`: Claude → `system.ai.claude-sonnet-5-5` (Anthropic Messages), Codex → `system.ai.gpt-5-5` (Responses), Gemini → `system.ai.gemini-3-8-flash`
  - [ ] `mcp_servers`: one demo MCP server
  - [ ] `skills`: the demo skill from Task 10, so the Skills tab shows loads
  - [ ] Unity Gateway features: Smart Routing and tracing, where supported
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

## Already in flight
- [ ] Fill in the harness traffic matrix in `docs/omni-fevm.md` once `system.ai_gateway.usage` catches up (it lags about 20 min).
- [ ] Re-run the native Claude Code check under `omni-fevm` (closed before its reply was captured).
