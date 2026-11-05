# Bakehouse demo runbook

One question, four harnesses, one gateway. Gemini 3.8 Flash in Antigravity (agy) leads; Claude Code,
Codex and pi follow with the same agent prompt and the same skills. Unity Gateway then shows where
every call went. Sources for each claim are in `docs/research/facts.md` (section *Bakehouse
analytics demo*). Detailed steps live in the per-demo READMEs:

| Piece | README | Recipes |
|---|---|---|
| Data, metric views, dashboard, Genie agent | `demos/bakehouse/README.md` | `just analytics-*` |
| Skills in Unity Catalog | `demos/skills/README.md` | `just skills-*` |
| Agents per harness | `demos/bakehouse-agents/README.md` | `just agent <harness>`, `just agents-*` |
| Usage, routing, lineage, traces | `demos/observability/README.md` | `just obs-*` |

## One-time setup (presenter)

1. Merge the PRs in this order: skills, then agents (the agent bundles link to `skills/`), then
   analytics and observability in either order.
2. `just analytics-validate && just analytics-deploy && just analytics-run`. Re-runs are safe and
   don't re-score reviews that already have a sentiment.
3. `just skills-sync`, twice. The second run should report every skill `unchanged`. Grant the
   audience group if needed: `just skills-grant <principal>`.
4. `just gateway-validate && just gateway-deploy` for the agents dashboard. The plan must show no
   deletes or recreates of model services.
5. `just agents-print-config` and apply what it prints yourself:
   - the `gemini-shim` provider as the default Gemini provider for Omnigent;
   - `"model": "Gemini 3.8 Flash (Medium)"` in `~/.gemini/antigravity-cli/settings.json`. Without
     it, agy opens on Gemini 3.1 Pro, which the workspace doesn't serve, and the turn ends empty.
6. Optional, Beta: Unity Gateway → Govern → Traces, pick the trace table, grant `SELECT`.
7. Optional: `ln -s ~/.config/cursor/chats ~/.cursor/chats` if you want Cursor sub-agents in
   Omnigent to show their transcripts (Omnigent reads the wrong directory under XDG).

## Day before

- Run every harness once (`just agent agy`, `claude`, `codex`, `pi`) with the stage question, so
  usage rows exist. They take up to about an hour to land.
- Open both dashboards (*Bakehouse sales and sentiment*, the agents dashboard) and every page once.
- Check the lineage graph for `bakehouse_sales_metrics`: samples → bakehouse tables → metric view
  is confirmed; dashboard and Genie edges are not yet. Only claim what you see.

## On stage

1. **Data and governance (Databricks UI).** The `omnigent_talk` schema: model services next to the
   bakehouse tables, metric views and three UC skills. Lineage from `samples.bakehouse`.
2. **Antigravity on Gemini.** `just agent agy`. If the header shows Gemini 3.1 Pro, run `/model`
   → Gemini 3.8 Flash first. Ask: *"Which franchise had the highest revenue, and what do its
   reviews say?"* agy uses the `bakehouse-analyst` skill on the metric views. Approve each tool
   call when prompted (native agy launches don't skip permissions).
3. **Switch harness, same agent.** The same question in `just agent claude`, then `codex`, then
   `pi`. Same prompt and skills; only the harness changes. pi runs on Claude because of the pi +
   Gemini tool-schema bug. Gemini is agy's job.
4. **Genie.** Ask the *Bakehouse analyst* Genie agent the same question, directly or through the
   `bakehouse-genie` skill.
5. **Unity Gateway.** `just obs-routing`: the `gemini_router` 80/20 split across Gemini 3.8 and
   3.7 Flash, plus fallbacks. `just obs-usage`: calls by `harness` and `agent_spec` tags.
   `just obs-lineage`. Then the agents dashboard.

## Don't say

- That agy loads Unity Catalog skills natively. Antigravity isn't on the supported-agents list;
  the demo gives agy the same skills from the repo.
- That the review sentiment went through `gemini_router`. `ai_query` can't call custom model
  services, so the batch job calls Gemini 3.8 Flash directly.
- Any `databricks-gemini-*` name. Show `system.ai.gemini-*`.

## Screen hygiene

- The agy shim's log line prints the full service name, including the catalog. Keep that terminal
  off screen.
- `just skills-list` shows skill ids only; `--full` adds the catalog. Don't use `--full` on stage.

## Fallbacks

- agy turn ends empty: `/model` → Gemini 3.8 Flash; failing that, run the same agent on Claude.
- No usage rows yet: show `just split-demo 10` live, which tallies the served model per call.
- Gemini 3.8 Flash slow or down: `system.ai.gemini-3-7-flash` (see `talk/prep-reference.md`).
