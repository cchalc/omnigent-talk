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

## Bakehouse analytics demo

Researched 2026-11-03/04 by sub-agents; *(paraphrase)* rows need a word-for-word check before they go on a slide.

| Claim | Quote / detail | URL | Status |
|---|---|---|---|
| Unity Catalog skills (Beta) | A skill is a UC object `catalog.schema.skill` built from a SKILL.md folder. Create (`POST /api/2.1/unity-catalog/skills?parent=schemas/<c>.<s>&skill_id=<id>`), upload files to `/api/2.0/fs/files/Skills/<c>/<s>/<skill>/`, then `finalize`. No version numbers; re-upload and finalize *(paraphrase)* | DBX/aws/en/ai-gateway/skill-reference | paraphrase; live sync of 3 skills worked on fevm-cjc 2026-11-03 |
| Skills have no IaC resource | "Skills don't have Terraform or Declarative Automation Bundles resources" *(paraphrase)*. Hence `just skills-sync` | DBX/aws/en/ai-gateway/govern-skills | paraphrase |
| Typed skills CLI needs v1.20 | `databricks ai-gateway create-skill` etc. need CLI ≥ 1.20; the demo machine has 1.17, so the sync uses REST | `databricks ai-gateway --help` (v1.17.0) | verified locally 2026-11-03 |
| Skill grants | Skills use volume privileges: `READ VOLUME` to consume, `CREATE VOLUME` + `WRITE VOLUME` to author *(paraphrase)* | DBX/aws/en/ai-gateway/govern-skills | paraphrase |
| Agents that load UC skills | Claude Code, Codex, Cursor (MCP only), Copilot, Gemini CLI, OpenCode, Pi. Antigravity is not listed *(paraphrase)* | DBX/aws/en/ai-gateway/coding-agent-supported-agents | paraphrase. Don't claim agy loads UC skills natively; the demo gives agy the same skills from the repo |
| Genie agents as code | `genie_spaces` is a bundle resource (direct engine); `serialized_space` inline or `file_path`. `databricks bundle generate genie-space` exports one *(paraphrase)* | DBX/aws/en/dev-tools/bundles/resources | paraphrase; deployed via `just analytics-deploy` 2026-11-03 |
| Metric views | No bundle resource; created with `CREATE OR REPLACE VIEW … WITH METRICS LANGUAGE YAML` from a bundle SQL task *(paraphrase)* | DBX/aws/en/metric-views/create | paraphrase; two metric views built 2026-11-03 |
| `ai_query` can't call custom model services | `ai_query` on a user-created UC model service fails (`AI_FUNCTION_COMPILATION_ERROR` / "not enabled"); Databricks-provided services work | DBX/gcp/en/ai-gateway/query-model-services | verified (URL 200, live probe 2026-11-03). So batch sentiment calls Gemini 3.8 Flash directly, not `gemini_router` |
| Router verification | `gemini_router` 10 calls: 7 Gemini 3.8 Flash / 3 Gemini 3.7 Flash (configured 80/20, fallback 3.5 Flash). `gemini_fast` 9/9, `gemini_general` 3/3, `qwen_code` 6/6 | `just split-demo 10`, `just probe`, fevm-cjc 2026-11-03; `demos/observability/README.md` | verified |
| Request tags | Header `Databricks-Ai-Gateway-Request-Tags: {json}` lands in `request_tags` in `system.ai_gateway.usage` and inference tables *(paraphrase)* | DBX/aws/en/ai-gateway/request-tagging | paraphrase; usage rows lag up to about an hour |
| Fallback in usage | A fallback is one usage row with `size(routing_information.attempts) > 1` (`INITIAL_ATTEMPT` then `FALLBACK`) | live `system.ai_gateway.usage`, 2026-11-04 | verified |
| Lineage entity types | Job-written tables show `entity_type = JOB`, dashboards `DASHBOARD_V3`; Genie shows through `entity_metadata.genie_space_id`, not an entity type | DBX/aws/en/admin/system-tables/lineage; live `system.access.table_lineage` 2026-11-04 | verified live (no `GENIE` entity type seen) |
| Bakehouse lineage | samples.bakehouse → `bakehouse_*` tables → metric views, attributed to the build job | live UC lineage, 2026-11-03 | verified. Dashboard and Genie edges not yet seen; check before claiming |
| Model service lineage | Foundation model (primary / fallback) → service → inference table *(paraphrase)* | DBX/aws/en/data-governance/unity-catalog/ai-gateway-service-lineage | paraphrase; needs an inference table attached |
| Custom-agent traces (Beta) | Agents can send OTLP spans to `<ws>/ai-gateway/otel/v1/traces`; `traceparent` joins gateway spans. Separate per-workspace Beta *(paraphrase)* | DBX/aws/en/ai-gateway/unified-trace-table | paraphrase; not set up |
| Bakehouse data | 6 tables: transactions 3,333, customers 300, franchises 48, suppliers 27, reviews 204, review chunks 196. May 2024. Revenue $66,471; avg transaction ≈ $19.94. Gemini sentiment: 106 positive / 88 negative / 10 mixed | `samples.bakehouse`, profiled 2026-11-03 | verified |
| Legacy Gemini endpoint name | `ai_query('databricks-gemini-3-8-flash', …)` worked in SQL on fevm-cjc 2026-11-03, but REST returns 403 (row above). Show `system.ai.gemini-3-8-flash` only | live probe 2026-11-03 | OPEN: keep the legacy name off slides |

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
| Agent bundle | A directory with `config.yaml`, `skills/<s>/SKILL.md`, `tools/mcp/*.yaml`; `omni run <dir>` runs it | local package `omnigent/spec/parser.py`, `spec/types.py` (0.22.0.dev0) | verified from source |
| Native harness is fixed per spec | `omni run AGENT --harness <x>-native` is rejected because native TUIs ignore the spec, so switching = one spec per harness | local `omnigent/cli.py` | verified from source |
| Skill discovery per harness | Claude: bundle + `.claude/skills` + `.agents/skills`; Codex: bundle + `$CODEX_HOME/skills` + `~/.agents/skills`; agy: workspace `.agents/skills`; pi: `--skill` | local omnigent harness sources | verified from source |
| agy default model gotcha | With no model set, agy picks Gemini 3.1 Pro, which FEVM doesn't serve; the turn ends empty. Fix: pin `gemini-3.8-flash`, or `/model` first | local `harnesses/antigravity_native/credentials.py`; runner logs 2026-11-03 | verified. Keep `/model` in the runbook |
| pi + Gemini tool-schema bug | pi's schema cleanup passes `type: [X, "null"]` through and Gemini rejects it (400) | local `inner/pi_executor.py` (0.22.0.dev0); repro 2026-11-03 | verified. Run pi on Claude, Gemini on agy |

## Agent behavior

| Claim | Quote / detail | URL | Status |
|---|---|---|---|
| Agent Behavior format | Behavior specs describe recurring conduct for trace review and evaluation, live under `.agents/behaviors/<name>/BEHAVIOR.md`, and version with the code they govern | https://agentbehavior.dev/ ; https://github.com/braintrustdata/agentbehavior | verified 2026-11-03 |
