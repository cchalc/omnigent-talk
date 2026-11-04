# Facts

Every on-stage claim, with its source. Quotes marked *(paraphrase)* came from WebFetch summaries and must be checked word-for-word before going on a slide (Task 2). `OPEN` means it's still unresolved.

Verified 2026-11-02 unless noted. `DBX` = `https://docs.databricks.com`.

## Databricks

| Claim | Quote / detail | URL | Status |
|---|---|---|---|
| Gemini 4 Argon on Unity Gateway (Oct 13 2026) | "Google Gemini 4 Argon is now available on Unity Gateway. You can access this model using Foundation Model APIs." | DBX/gcp/en/release-notes/unity-gateway/#google-gemini-4-argon-is-now-available-on-unity-gateway | verified |
| Gemini 3.8 Flash Databricks-hosted (Sep 2 2026) | "Model Serving now supports Google Gemini 3.8 Flash as a Databricks-hosted model." | DBX/gcp/en/release-notes/unity-gateway/ | verified |
| Gemini 3.7 Flash on Unity Gateway (Aug 13 2026) | "…for fast, cost-efficient everyday tasks." | DBX/gcp/en/release-notes/unity-gateway/ | verified |
| Gemini model names | UC model services `system.ai.gemini-3-1-flash-lite`, `system.ai.gemini-3-5-flash`, `system.ai.gemini-3-7-flash`, `system.ai.gemini-3-8-flash` on fevm-cjc. Argon not present there | probe 2026-11-02 | verified for fevm-cjc; Argon is mention-only (decision 11), so no name needed |
| Smart Routing (Beta) | "automatically picks the right model and agent harness for each task, based on complexity, permissions, and budget"; "works with Claude Code and Codex when you run them through the Unity Gateway CLI or Omnigent" | DBX/gcp/en/ai-gateway/coding-agent-model-selection | verified |
| Smart Routing details | Lowest-cost capable `system.ai.*` model. Subagents routed independently. Needs the Enhanced Unity Gateway account preview and `EXECUTE` on candidates. Omnigent ≥0.8: UI "Smart Routing" harness, `omni claude --smart-routing --server <ws>`. `--model` disables it *(paraphrase)* | same | verified |
| Usage table coding-agent metadata (Sep 27 2026) | "The `system.ai_gateway.usage` system table now includes coding-agent session metadata and invocation source." | DBX/gcp/en/ai-gateway/usage-tracking | verified |
| Usage table columns | `event_time, requester, requester_type, endpoint_name, destination_model, invocation_metadata, input_tokens, output_tokens, total_tokens, token_details, latency_ms, time_to_first_byte_ms, status_code, routing_information, mcp_metadata, session_metadata{client_session_id, client_subagent_id, coding_agent, agent_version, surface, reasoning_effort, smart_router_name}, request_tags, auth_mode`. No cost column | same | verified (re-check with DESCRIBE, Task 9) |
| Usage dashboard tabs | Overview, Spend, Coding Agents, MCPs, Skills, Performance, README | DBX/gcp/en/ai-gateway/usage-tracking#built-in-usage-dashboard | verified |
| Skills tab (Oct 30 2026) | "The **Skills** tab of the usage dashboard shows downloads, loads, and activity by user." | DBX/gcp/en/ai-gateway/usage-tracking#view-usage-dashboard | verified |
| Skills REST API (Beta, Oct 12 2026) | "The Unity Gateway Skills REST API is now available in Beta" | DBX/gcp/en/ai-gateway/skill-reference | verified |
| Skills audit logs (Oct 30 2026) | "Audit logs record skill list, load, and file fetch events under the `aiGatewaySkills` service." | DBX/gcp/en/admin/account-settings/audit-logs#ai-gateway-skills | verified |
| Central coding-agent config (Sep 22 2026) | "Organizations can now centrally configure coding agents: models, MCP servers, skills, a default harness" | DBX/gcp/en/ai-gateway/coding-agent-configure-govern | verified |
| Coding-agent config schema | Agent enums are only `CODING_AGENT_CLAUDE_CODE` and `CODING_AGENT_CODEX` (no Gemini CLI). Per agent: one model source (`model_services` / `model_provider_service` / `unity_catalog_location`), `default_models` (Claude also `default_{opus,sonnet,haiku,fable}_model`), `smart_routing.enabled`, `tracing.enabled`, `http_headers`. Top level: `mcp_servers`, `skills`, `smart_defaults{budget_id, tiers}` | DBX/aws/en/ai-gateway/coding-agent-config-schema | verified 2026-11-03 |
| `ug` CLI (Sep 22 2026) | "Use the Unity Gateway CLI (`ug`) to connect Claude Code, Codex, Pi, and more to Unity Gateway with one command." | DBX/gcp/en/ai-gateway/coding-agent-quickstart | verified |
| Gemini CLI supported | `ug gemini`. Antigravity not listed | DBX/gcp/en/ai-gateway/coding-agent-supported-agents | verified |
| Native Gemini API route on Unity Gateway | `POST <ws>/ai-gateway/gemini/v1beta/models/system.ai.gemini-3-8-flash:generateContent` (Bearer) returns a Gemini-native response incl. `thoughtSignature`. Omnigent's agy adapter uses this route | probe on fevm-cjc workspace, 2026-11-02; omnigent `harnesses/antigravity_native/gateway.py` | verified |
| Legacy Gemini endpoints retired | `databricks-gemini-3-8-flash` → 403 "is no longer available. Use Unity Catalog model services." Use `system.ai.gemini-*` | probe on fevm-cjc, 2026-11-02 | verified |
| Unified trace table (Beta, Aug 21 2026) | "It captures every request and response across your Unity Gateway services into one Unity Catalog table" | DBX/gcp/en/ai-gateway/unified-trace-table | verified |
| Coding-agent tracing (Sep 22 2026) | "Unity Gateway now adds coding-agent activity to unified tracing through the Unity Gateway CLI" | DBX/gcp/en/ai-gateway/coding-agent-observability#tracing | verified |
| Inference tables | "Attach inference tables to log full request and response payloads to a governed Delta table." | DBX/gcp/en/ai-gateway/model-provider-services | verified |
| Usage tracking on by default (Jul 17 2026) | "…token counts, latency, and cost attribution per user, team, or app." | same | verified |
| Sensitive Data Detection guardrail (Beta) | "detects structured sensitive data". Blocked calls return HTTP 200 with the block reason | DBX/gcp/en/data-governance/unity-catalog/service-policies/detect-sensitive-data | verified |
| MCP prompt-injection screening (Beta, Oct 21 2026) | "screen MCP tool calls and their results in Unity Gateway for jailbreak and prompt injection attempts" | DBX/gcp/en/data-governance/unity-catalog/service-policies/create-service-policy#use-a-built-in-policy | verified |
| Budgets / rate limits (Oct 15 2026) | "account admins can set budgets and rate limits, or disable direct model access" | DBX/gcp/en/ai-gateway/rate-limits, /budgets | verified |
| Omnigent on Databricks | Beta. "a common layer over Claude Code, Codex, Cursor, Pi, and the agents you write yourself". Managed server with workspace IdP; models via FMAPI and Unity Gateway; Sandbox hosts in select AWS regions *(paraphrase)* | DBX/aws/en/omnigent/ ; DBX/gcp/en/omnigent/ | verified |
| Managed Omnigent policy limit | Built-in and CEL custom policies only. "Custom Python policies are not supported." | DBX/gcp/en/omnigent/ | verified |
| Omnigent on Databricks quickstart | `omni login <workspace-url>`, `omni host --server <workspace-url>`; sessions at `<workspace-url>/omnigent` *(paraphrase)* | DBX/aws/en/omnigent/quickstart | verified |
| Omnigent workspace prerequisite | "The Omnigent preview enabled for your workspace." The workspace must be in a Unity Gateway region, and Sandbox hosts also need the Sandbox preview and region | DBX/aws/en/omnigent/quickstart | verified 2026-11-02 |
| Workspace-hosted Omnigent mount | API at `<ws>/api/2.0/omnigent`. `GET …/v1/me` is the probe `omni login` uses. 200 = enabled; FEVM returned 404 before the preview was on | omnigent `cli.py` `_workspace_mount_probe_matches`; probe 2026-11-02 | verified |
| FEVM demo workspace (`fevm-cjc`) | AWS `us-east-1`. Gemini 3.1 Flash Lite / 3.5 / 3.7 / 3.8 Flash available, **no Gemini 4 Argon**. Presenter is a workspace admin and can read `system.ai_gateway.usage`. No unified trace table yet | probe 2026-11-02 | verified |
| Claude Code org-managed settings pin the gateway | On the presenter's laptop, managed settings set `ANTHROPIC_BASE_URL` and `apiKeyHelper` to the org (ai-devtools) gateway, which overrides per-session wrappers. Device-level governance, and a talk point | local `managed-settings.json`, 2026-11-02 | verified (per-harness effect OPEN) |
| Agent memory and sessions | GCP page exists (updated Oct 14 2026). Sessions = one interaction's state; memory = durable facts recalled in later conversations; memory pipelines distill sessions *(paraphrase)* | DBX/gcp/en/agents/custom-agents/stateful-agents | verified |
| Managed memory API (Beta) | `pip install databricks-agentbricks` (≥0.6.0); `AgentKitClient(WorkspaceClient()).memory_stores.create("support-agent-memory")`; `.add/.put(actor_id=, path=, content=, description=)`; `.search(actor_id=, query=, limit=)`. Hybrid BM25 + semantic search, ≤100 results. `actor_id` is not access control. Pay for the underlying Lakebase | DBX/gcp/en/agents/agent-memory/managed-memory | verified; import name `databricks_agentkit` vs package name OPEN |
| Databricks Sandbox (Beta) | Serverless on-demand compute for untrusted or AI-written code. 4 vCPU / 8 GB, 100 GB home (`/home/sandbox-agent`), 24 h cap, ingress closed, **egress unrestricted**, 1 h auto-refreshed credential | DBX/aws/en/compute/serverless/sandbox | verified |
| Sandbox on GCP | GCP page returns 404 | DBX/gcp/en/compute/serverless/sandbox | verified: not on GCP (2026-11-02) |
| Sandbox SDK | `w.sandbox.create_sandbox(sandbox_id=...)`, `w.sandbox.execute_command_sync(args=["-c", ...], execution_timeout=Duration(seconds=30))`, `resp.exit_code`, `resp.stdout`, `w.sandbox.delete_sandbox("sandboxes/<id>")`. CLI: `databricks sandbox create / register / ssh`. Agent Bricks: `agentbricks tools add sandbox --scope table:...` | DBX/aws/en/compute/serverless/sandbox-quickstart | verified (exact signatures OPEN) |

## Omnigent

| Claim | Quote / detail | URL | Status |
|---|---|---|---|
| Harness tiers and modes | 18 harnesses in 3 tiers. Fully supported: `claude-sdk`, `codex`, `openai-agents`. Direct (Omnigent runs model + tools) vs Native TUI (`*-native`) *(paraphrase)* | https://omnigent.ai/docs/build/harnesses/supported | verified |
| Antigravity tier | community-supported | same | verified |
| Antigravity harness | `antigravity-native`, `omni agy` (v0.12+), aliases `agy`, `google-antigravity` | https://omnigent.ai/docs/build/harnesses/configuration#antigravity | verified |
| agy install | `curl -fsSL https://antigravity.google/cli/install.sh \| bash`; "requires agy 1.1.13 or newer" | same | verified |
| Native agy creds | `omni setup` → Antigravity → "Configure native agy API key / gateway" → Databricks profile writes `native_gemini: true`. Native Gemini API required; OpenAI Responses / Chat Completions "not supported"; Bearer / token-refresh gateways unsupported | https://omnigent.ai/docs/build/harnesses/configuration#configure-native-agy-credentials | verified |
| agy cred locations | Keychain (agy ≥1.1.7), `~/.gemini/oauth_creds.json` (macOS, ≤1.0.10), `~/.gemini/antigravity-cli/antigravity-oauth-token` (Linux) | same | verified |
| Routing config | `llm: {model, connection, profile, fallback_models, request_timeout}` or `routing: {provider: external, base_url, router_name, model_prefix, api_key, profile}`. With neither, Auto picker hidden. No dry-run | https://omnigent.ai/docs/reference/configuration/routing | verified |
| Policy YAML | `policies: <name>: {type: function, handler, factory_params, on: [...]}`; server key `policy_modules` | local package `omnigent/policies/schema.py`, `inner/loader.py` (docs page 404) | verified from source; docs OPEN |
| CEL policy | `handler: omnigent.policies.builtins.cel.cel_policy`, `factory_params: {expression, reason}`. Expression sees `event`, returns `{"result": "DENY"\|"ASK"\|"ALLOW", "reason"}`. `tool_call` data = `{name, arguments}`. `event.context.model`, `.harness` | local package `policies/builtins/cel.py`, `policies/schema.py` | verified from source |
| Built-in policies | `cost_budget(max_cost_usd, ask_thresholds_usd, expensive_models)`, `user_daily_cost_budget`, `subagent_cost_budget`, `max_tool_calls_per_session`, `github_policy`, `deny_trivial_to_expensive_model(expensive_models)`, `block_working_dir_changes`, `blast_radius`, `risk_score_policy`, `cel_policy`, `ask_on_os_tools` | local package `policies/builtins/` | verified from source |
| Collaboration | Share → Read / Edit; Edit collaborators "co-drive" (messages labeled with the collaborator's email); `omni attach <session_id>` | https://omnigent.ai/docs/collaborate | verified; inline comments not documented |
| Mobile | Android `ai.omnigent.android` (Google Play), iOS App Store, installable PWA | https://omnigent.ai/docs/interact/mobile | verified |
| Project config | `.omnigent/config.yaml` in cwd overrides `~/.omnigent/config.yaml`; only `harness` is deep-merged | `omni config --help`; local `config.py` | verified |
| Agent YAML | `name`, `prompt`, `executor.{harness, model, auth}`, `policies`; no `extends` | https://github.com/omnigent-ai/omnigent/blob/main/docs/AGENT_YAML_SPEC.md | verified; `executor.harness` vs local parser OPEN |
| Latest release | v0.20.0 (2026-10-28) | https://github.com/omnigent-ai/omnigent/releases | verified |
| Full scope | Polly / Debby bundled agents, scheduled tasks, inbox / async calls, browser tools, skills, Slack (`omni integration slack`), cloud sandboxes (`omni sandbox`: modal / daytona / islo), REST API, macOS app, mobile | https://github.com/omnigent-ai/omnigent ; https://omnigent.ai/ ; `omni --help` | verified |
| Where the agent picker's entries come from | `sys_agent_list` merges `builtins` (`GET /v1/agents`), `session_agents` (one row per session) and `local_configs` (`<cwd>/.omnigent/agent-configs/*.yaml`, top level only) | local package `omnigent/runner/tool_dispatch.py:638,5797,5990` (0.22.0.dev0) | verified 2026-11-03 |
| Polly and debby are packaged bundles | Seeded at server start from `omnigent/resources/examples/{polly,debby}/`, filtered by `OMNIGENT_SEEDED_AGENTS` | local package `omnigent/server/app.py:1424,1492`, `server/seeded_agents.py:20` | verified 2026-11-03 |
| "unconfigured" native cards | Host readiness: `False` or missing means `unconfigured`. Also `binary-missing`, `version-too-low`, `needs-auth` | local package `omnigent/harness_availability.py:36-53` | verified 2026-11-03 |
| Custom agents via `omnigent agent add` | Uploads a bundle dir as a user agent (re-add replaces it). It is listed by `omnigent agent list`, not in `sys_agent_list` builtins | local package `omnigent/cli.py:12468`, `server/routes/builtin_agents.py:452`; observed with rory on FEVM | verified 2026-11-03 |
| Bundle env expansion is partial | `${VAR}` is expanded only in connection, api_key auth and MCP fields, not `executor.model` / `auth.profile` | local package `omnigent/cli.py:6525` | verified 2026-11-03 |
| openai-agents harness on a UC model service | `executor.model: <catalog>.<schema>.qwen_code`, `auth: {type: databricks, profile}`, `use_responses: false` returns Qwen chat completions | spike + rory session on FEVM, 2026-11-03; `omnigent/inner/openai_agents_sdk_executor.py:563` | verified 2026-11-03 |

## Agent behavior

| Claim | Quote / detail | URL | Status |
|---|---|---|---|
| Agent Behavior format | Behavior specs describe recurring conduct for trace review and evaluation, live under `.agents/behaviors/<name>/BEHAVIOR.md`, and version with the code they govern | https://agentbehavior.dev/ ; https://github.com/braintrustdata/agentbehavior | verified 2026-11-03 |
