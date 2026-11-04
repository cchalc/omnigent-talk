# `ug` managed coding-agent configuration (draft)

`coding-agent-config.json` is the body for the workspace's one published Unity Gateway coding-agent configuration. It's the admin-side counterpart to Omnigent: it decides which agents, models, MCP servers and skills every developer gets when they run `ug`.

Schema: https://docs.databricks.com/aws/en/ai-gateway/coding-agent-config-schema (Beta). This repo is public, so the file has no workspace hosts or IDs.

## What's in it
- `default_agent`: the agent a bare `ug` launches. It must be in `enabled_agents`.
- `enabled_agents`: Claude Code and Codex. These are the only two agent enums (`CODING_AGENT_CLAUDE_CODE`, `CODING_AGENT_CODEX`), so **Gemini CLI can't be configured here**.
- `config.models.model_services`: a static list of `system.ai.*` model services. Each agent sets exactly one model source. The others are `model_provider_service` and `unity_catalog_location`.
- `config.default_models`: `default_model` works for every agent. Claude Code also takes `default_{opus,sonnet,haiku,fable}_model`. With a static list, every default must also appear in `model_services`.
- `smart_routing` / `tracing`: per-agent Unity Gateway features. Smart Routing applies to subagent tasks where supported.
- `http_headers`: a demo tag. Every developer can see these values, so never put secrets here. Reserved headers (`Authorization`, `Cookie`, `Host`) are rejected.
- `mcp_servers` / `skills`: Unity Catalog names. **Placeholders:** `omnigent_talk.demo` and `<mcp-server>` must point at real resources before publishing. `gcp-databricks-facts` is the Task 10 skill.

## Before publishing
1. Enable the **Unity Gateway Managed Configuration** preview (Settings → Previews). This needs a workspace admin.
2. Confirm `system.ai.claude-opus-5-5` and `system.ai.claude-haiku-5-5` are served on the workspace. Only `claude-sonnet-5-5` and `gpt-5-5` have been checked (`docs/setup-log.md` §6). If either isn't served, drop it and its default key.
3. Replace the MCP and skill placeholders.
4. Grant `EXECUTE` on the model services to the demo user or group. Developers also need the **Workspace access** or **Consumer access** entitlement to read and apply the config.
5. Model services must speak the agent's API: Claude Code needs Anthropic Messages, and Codex needs Open/OpenAI Responses. Both are verified on FEVM (`/ai-gateway/anthropic/v1/messages` and `/ai-gateway/codex/v1/responses` returned 200, `docs/setup-log.md` §6).

## Publish / update
```bash
databricks api post /api/ai-gateway/v2/coding-agent-configs \
  --profile fevm-cjc --json @config/ug/coding-agent-config.json

# update: use the returned `name` and list the changed fields
databricks api patch "/api/ai-gateway/v2/coding-agent-configs/<name>?update_mask=enabled_agents" \
  --profile fevm-cjc --json @config/ug/coding-agent-config.json
```
Or publish in the UI: **Unity Gateway → Govern → Agent configuration → Edit configuration**, paste the JSON, then **Format JSON** → **Save**. The workspace has one published config, so when editing keep the settings you still need.

Then, on the developer side, run `ug configure` and `ug claude` / `ug codex`.

How updates reach developers: each `ug` launch re-checks the config and applies **agent and model** changes, which can take a few minutes. **MCP servers and skills** only sync on `ug configure`. That matters for the demo: if you change `default_model`, relaunching is enough, but if you add a skill, run `ug configure` first.

## Optional: smart defaults (once a budget exists)
Add this at the top level. It switches the default agent and model as spend against the budget rises. `budget_id` is the budget's `budget_configuration_id`.
```json
"smart_defaults": {
  "budget_id": "<budget_configuration_id>",
  "tiers": [
    { "spending_percentage": 0.8, "recommended_agent": "CODING_AGENT_CODEX", "recommended_model": "system.ai.gpt-5-5" }
  ]
}
```
