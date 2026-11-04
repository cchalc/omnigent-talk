# Backup appendix

Backup slides for the 20-minute talk. None of them is presented. Each one is there if a question lands on it, or if a live beat runs out of time.

**Readiness labels:**
- **ready**: the recipe has run on the demo workspace, the output is recorded, and the claims are sourced.
- **partial**: some of it is built or run, but a required step is missing (named in the item).
- **not built**: nothing in the repo yet beyond a plan entry.

**Labels in the slides:** Beta features carry "(Beta)" on the slide. Antigravity is **community-supported**. Sandbox is **AWS only**. Product name is **Unity Gateway** (CLI `ug`). Models are `system.ai.*`.

**Shared rules:** nothing here puts a workspace host, ID, or email on screen. Use `$DBX_PROFILE` in commands. Don't show scores from the behavior evals (none exist).

---

## A1. Agent memory (Beta)

**Slide title:** Agents that remember (Beta)

**On-slide text:** Durable facts, not chat logs. Recalled in a later session. Scoped by actor. Managed store on Lakebase. Beta.

**Speaker notes:**
- Sessions hold one interaction's state. Memory holds the facts an agent should recall later. Say the difference first, then show the store.
- The claim to make is "remember in one process, recall in another." That isn't recorded in the repo yet, so keep the on-stage demo to the recall step only if a run is captured.
- `actor_id` scopes recall. It is **not** access control. Isolate with one store per trust boundary.
- You don't set up Lakebase; creating the store provisions it. You do pay for the Lakebase underneath.

**Recipes** (`.env.local` needs `DBX_PROFILE` and `MEMORY_STORE`; the `just` recipes add `--extra memory`):

```bash
just memory-create                         # find the store by display name, or create it
just remember "prefers Gemini" presenter   # store one fact
just recall "which model?" presenter       # expect the fact back
just recall "which model?" someone-else    # expect "(nothing recalled for someone-else)"
```

**Facts rows:** "Agent memory and sessions"; "Managed memory API (Beta)".

**Readiness: partial.**
- Built: `src/omnigent_talk/memory.py` (remember is idempotent by fact hash; recall is filtered by actor). `tests/test_memory.py` checks both against a fake store, offline.
- Commit `01d0ad3` says remember and recall were verified on the FEVM demo workspace. There's no transcript in the repo.
- Missing: a recorded cross-process run (remember in one process, recall in another).

**Flags:**
- The SDK names differ from the facts row. The code calls `memory_stores.create(name, description=...)` and reads `MemorySearchResult(memory=Memory(content=...))`. The facts row shows `create("support-agent-memory")` and says the import name (`databricks_agentkit`) is OPEN.

---

## A2. Databricks Sandbox (Beta, AWS only)

**Slide title:** Throwaway compute for code the agent wrote (Beta, AWS)

**On-slide text:** Serverless sandbox per run: 4 vCPU, 8 GB, 24 h cap. Ingress closed. Egress open. AWS only. Beta.

**Speaker notes:**
- Each run creates a fresh sandbox, runs the command under bash, then deletes the sandbox, even on failure.
- Say "isolated from my laptop," never "isolated from the network." Egress is unrestricted, per the facts row.
- Sandbox is AWS-only today. The GCP docs page returns 404. Say so on the slide.
- The stage moment is the output: `45` then `[exit 0]`, followed by the isolation check.

**Recipes:**

```bash
just sandbox-run "python3 -c 'print(sum(range(10)))'"   # expect: 45, then [exit 0]
just sandbox-isolation                                    # expect: home=/home/sandbox-agent (whoami output not recorded)
```

**Facts rows:** "Databricks Sandbox (Beta)"; "Sandbox on GCP"; "Sandbox SDK".

**Readiness: partial.**
- Built: `src/omnigent_talk/sandbox.py`. `tests/test_sandbox.py` checks the call order (create, execute under bash, delete) and that a failing command still deletes the sandbox. Uses a fake API.
- Commit `01d0ad3` says "sandbox run and isolation" were verified on the FEVM demo workspace. There's no recorded output in `docs/` or the demo README.
- Missing: a live run with recorded output. The fallback threshold (below) can't be set until one exists.

**Flags:**
- `sandbox.py` passes `sandbox=Sandbox()` *and* `sandbox_id=` to `create_sandbox`. The facts row shows only `sandbox_id`. Signature is OPEN.
- `demos/model-services/README.md` says the sandbox home "ships with `.claude`, `.codex`, `.omnigent` and `.databrickscfg`." No source. Don't say it on stage.
- "Its own identity" (`sandbox-agent`) is in the code's docstring, not in the facts rows. Use the home path only, which the facts row has.

---

## A3. Budgets (Unity Gateway)

**Slide title:** A monthly cap on Unity Gateway spend

**On-slide text:** Per-user monthly cap on Unity Gateway. Block past the threshold or send an alert. An account admin applies it.

**Speaker notes:**
- The repo builds the budget body and prints it. Nothing is applied from here. The apply step needs an account admin.
- A per-user block on a shared workspace would stop everyone. So the default targets only the caller, and everyone else gets a high threshold.
- The sourced fact is short: account admins can set budgets and rate limits. Don't say more than that on stage.
- Don't say "budget per model." Services carry no tags. That claim has no source yet (see below).

**Recipes** (prints the body; nothing is created):

```bash
just budget 0.50                  # body for a $0.50 per-user block, caller only
just budget 0.50 --alert-only     # email instead of blocking
just budget 0.50 --everyone       # every user (not on a shared workspace)
```

Apply, by an account admin, with an account-level profile (`account_id` and `workspace_id` must be set on the profile):

```bash
databricks account budgets create --json @budget.json --profile <account-profile>
```

**Facts rows:** "Budgets / rate limits (Oct 15 2026)". That's the only budget row.

**Readiness: partial.**
- Built: `src/omnigent_talk/budget.py`, with `tests/test_budget.py`. The tests check the body against the code's own constants. They don't check it against the API.
- Not applied. Nothing has been created in any account.

**Unsourced claims. Verify each against the budgets API doc before on stage:**
1. Resource type `BUDGET_RESOURCE_TYPE_UNITY_AI_GATEWAY`.
2. Scope `ALERT_CONFIGURATION_SCOPE_TYPE_PER_USER`. The per-user semantics: each user measured separately.
3. Enums `CUMULATIVE_SPENDING_EXCEEDED`, `MONTH`, `LIST_PRICE_DOLLARS_USD`.
4. Actions `BLOCK_USAGE` and `EMAIL_NOTIFICATION`. The UI label "Block usage."
5. `principal_overrides` with `principal_id` and `override_threshold`, and the claim that an override changes only the threshold.
6. Filter `workspace_id` with operator `IN`.
7. "A budget can't be narrowed to one model service (services carry no tags)."
8. The `EVERYONE_ELSE_USD = 100000` placeholder. That's a design choice, not a documented limit.
9. The `databricks account budgets create` command and the requirement that the profile has `account_id` and `workspace_id` set.
10. Enforcement latency: how soon a block takes effect after the threshold is crossed.

---

## A4. Managed coding-agent config (`ug`)

**Slide title:** Admin sets the defaults. Developers run `ug`.

**On-slide text:** One published config per workspace: the agents, models, MCP servers and skills each developer gets from `ug`. Beta.

**Speaker notes:**
- Omnigent switches harnesses on the developer's side. Managed config is the admin's side: it decides the defaults before the developer picks anything.
- Only two agent enums exist: Claude Code and Codex. Gemini CLI can't be set here, so Antigravity stays an Omnigent harness.
- The draft lists Opus and Haiku 5.5 as model services. Neither is checked as served yet. Say "the draft," not "the config."
- Agent and model changes reach a developer on relaunch. MCP servers and skills need `ug configure`. That sync claim isn't sourced yet.

**Recipes:** no `just` recipe exists.

```bash
jq . config/ug/coding-agent-config.json                  # offline: valid JSON
# publish (not run; needs a workspace with the preview on, and an admin):
databricks api post /api/ai-gateway/v2/coding-agent-configs --profile "$DBX_PROFILE" --json @config/ug/coding-agent-config.json
```

Developer side, after publishing: `ug configure`, then `ug claude` or `ug codex`.

**Facts rows:** "Central coding-agent config (Sep 22 2026)"; "Coding-agent config schema"; "ug CLI (Sep 22 2026)"; "Smart Routing details" (the `smart_routing` field).

**Readiness: partial.**
- Built: `config/ug/coding-agent-config.json` (draft) and `config/ug/README.md` (publish and placeholder steps).
- Probe 2026-11-03 (`todo.md`): the GET endpoint on the demo workspace returns `{}`. Reachable, nothing published.
- Not done: the **Unity Gateway Managed Configuration** preview is not enabled. Nothing published. `EXECUTE` not granted. No budget. No propagation test.
- Placeholders still in the draft: `omnigent_talk.demo.<mcp-server>` and the skill `omnigent_talk.demo.gcp-databricks-facts`, which isn't built (see A6).

**Unsourced claims in the README and draft:**
1. The preview name "Unity Gateway Managed Configuration" and its location under Settings → Previews.
2. Developers need the "Workspace access" or "Consumer access" entitlement to read and apply the config.
3. MCP servers and skills sync only on `ug configure`. Agent and model changes apply on relaunch within "a few minutes."
4. "The workspace has one published config."
5. `http_headers` values are visible to every developer. Reserved headers (`Authorization`, `Cookie`, `Host`) are rejected.
6. Claude Code needs Anthropic Messages and Codex needs OpenAI Responses. Partly backed by the probe in `docs/setup-log.md` §6, but the requirement itself is not sourced.

---

## A5. Unity Gateway Smart Routing (Beta)

**Slide title:** Smart Routing (Beta): the cheapest capable model, per subagent

**On-slide text:** Smart Routing (Beta) picks the lowest-cost capable model for each subagent. Claude Code and Codex only.

**Speaker notes:**
- Not built here. Plan Task 7 hasn't run. Say "planned" or "in the product," not "in our demo."
- Our own router (N3) is a different mechanism: client-side, by prompt, with a Gemini classifier. Don't blur the two.
- Routing is nondeterministic and has no dry run. Assert the set of models a session may use, never the exact pick.
- The Enhanced Unity Gateway preview is an account-admin action. The presenter decides whether it's on.

**Recipes** (plan Task 7; not written, since `demos/03-routing/` doesn't exist):
- Start a session with **Smart Routing** as the harness in the web UI, or run `omni claude --smart-routing --server "$OMNI_SERVER"`.
- Check routing with the plan's query, which reads `session_metadata.smart_router_name` and `routing_information` from `system.ai_gateway.usage` for one session.

**Facts rows:** "Smart Routing (Beta)"; "Smart Routing details"; "Usage table coding-agent metadata" (for `smart_router_name`).

**Readiness: not built.**
- No `demos/03-routing/` directory, no session run, and the plan's Task 7 steps are unchecked.
- The Enhanced Unity Gateway preview is unconfirmed (plan "Still Open").

---

## A6. Skills on Databricks (Beta)

**Slide title:** Skills, governed like models (Beta)

**On-slide text:** Skill downloads, loads and audit events, per user. Dashboard Skills tab. Audit trail under the aiGatewaySkills service. Beta.

**Speaker notes:**
- The dashboard's Skills tab shows downloads and loads by user. That shipped in the Oct 30 release notes.
- Audit logs record list, load and file-fetch events under the `aiGatewaySkills` service.
- The REST API is Beta. Don't put the endpoints on a slide as stable.
- Not built: no skill is registered and no harness has loaded one yet. Say "planned" until a load shows in the dashboard.

**Recipes** (plan Task 10; not built):
- Write a small skill at `demos/06-skills/skills/gcp-databricks-facts/SKILL.md`.
- Register it through the Skills REST API (`ai-gateway/skill-reference`), or through the central config (`skills.names` in `config/ug/coding-agent-config.json`).
- Load it from `claude-sdk` and from Antigravity through Omnigent. Then check the Skills tab and `system.access.audit` for `service_name = 'aiGatewaySkills'`.
- Fallback if a harness can't load gateway skills: Omnigent's own `load_skill` path (plan Task 10 Step 4).

**Facts rows:** "Skills tab (Oct 30 2026)"; "Skills REST API (Beta, Oct 12 2026)"; "Skills audit logs (Oct 30 2026)".

**Readiness: not built.**
- No `demos/06-skills/`. The only trace is a placeholder skill name in `config/ug/coding-agent-config.json`.
- Plan Task 10 steps are unchecked.

---

## A7. Unified trace table (Beta)

**Slide title:** One trace table for every gateway call (Beta)

**On-slide text:** Every request and response across Unity Gateway services, in one Unity Catalog table. Beta.

**Speaker notes:**
- The quote is from the Aug 21 2026 release notes. Quote it word for word from the facts row, not from memory.
- It's not enabled on the FEVM demo workspace. Until it is, the demo uses `system.ai_gateway.usage`, which holds counts and metadata. Per the facts column list, it has no request or response payload columns. Re-check with DESCRIBE before saying that out loud.
- Use "unified trace table," not "MLflow traces." The plan corrected that wording.
- Full payloads: inference tables are the other route (facts row "Inference tables").

**Recipes:** no trace recipe exists (`demos/05-tracing/traces.md` isn't written). The usage-side recipes that do exist:

```bash
just usage-sql                    # routing per service, from system.ai_gateway.usage
just routing-metrics              # per service, route and served model
```

The plan's first step is to look for the trace table under AI Gateway → Govern → Traces on the demo workspace. If that needs metastore admin, fall back to usage plus inference tables (plan "Still Open").

**Facts rows:** "Unified trace table (Beta, Aug 21 2026)"; "Coding-agent tracing (Sep 22 2026)"; "Inference tables"; "Usage table columns".

**Readiness: not built.**
- Not enabled on the FEVM demo workspace. The "Unified trace table on FEVM" item in `todo.md` is unchecked.
- Whether the presenter's account can enable it without metastore admin is unresolved.

---

## A8. Behavior evals (synthetic, not run)

**Slide title:** Behavior specs for the agents that built this talk

**On-slide text:** Four written behavior specs govern the agents that built this talk. The evaluation harness exists. No scores yet.

**Speaker notes:**
- The trajectories are synthetic. They're hand-written pass and fail examples with known labels. A judge scoring them tests the judge, not the agents.
- No run is recorded. Don't show scores, run IDs, or agreement numbers. Plan Task 15 Step 5 asks for them, and it isn't done.
- Say "four written specs and a harness." Don't say "we evaluated the agents."
- The specs use the agentbehavior.dev format, sourced in the facts row "Agent Behavior format."

**Recipes** (opt-in; these create MLflow state and spend judge tokens; not run):

```bash
uv run pytest tests/test_behaviors.py    # offline: spec structure and corpus shape only
just behavior-eval-setup                 # needs DBX_PROFILE, BEHAVIOR_EVAL_EXPERIMENT, BEHAVIOR_JUDGE_MODEL
just behavior-eval-smoke                 # five cases
just behavior-eval                       # sixty cases, fifteen per behavior
```

`just check` runs the offline tests but not the MLflow run. It doesn't touch the workspace.

**Facts rows:** "Agent Behavior format" (verified 2026-11-03).

**Readiness: partial.**
- Built: `src/omnigent_talk/behavior_eval.py`, `scripts/behavior_eval.py`, `tests/test_behaviors.py`. The tests check spec structure, that the corpus has 60 cases (15 per behavior, balanced yes and no), and that the smoke set has 5.
- Not built: any workspace run. Plan Task 15 Steps 5 and 6 are unchecked.

---

## A9. Contextual policies in CEL (managed Omnigent)

**Slide title:** Policies that read the tool call

**On-slide text:** Managed Omnigent allows built-in and CEL policies only. A CEL rule can deny a tool call by its arguments and model.

**Speaker notes:**
- Managed Omnigent rejects Python policies. Residency is written as a CEL expression over the tool-call arguments.
- The policy event has no working directory. So a rule about a `customer-data/` path matches on the argument text, not on the directory.
- The plan's test idea: run the same CEL text offline against the real factory. Not built yet.
- The gateway side is separate. Sensitive Data Detection (Beta) returns HTTP 200 with the block reason. Say "200 with a block reason," not "a 4xx."

**Recipes** (plan Task 8; not built):

```bash
bash scripts/check.sh                                      # does NOT run policy tests yet; the plan says it should
cd policies && uv run pytest -q                            # planned: CEL tests, not written
```

Planned files: `config/omnigent/policies.yaml` (the CEL expression, using `event.data.arguments` and `event.context.model`), `policies/tests/test_cel_policies.py`, `demos/04-policies/run.sh`.

**Facts rows:** "CEL policy"; "Managed Omnigent policy limit"; "Built-in policies"; "Policy YAML"; "Sensitive Data Detection guardrail (Beta)"; "MCP prompt-injection screening (Beta, Oct 21 2026)".

**Readiness: not built.**
- No `config/omnigent/`, no `policies/`, no `demos/04-policies/`.
- Open question from the plan: whether the pinned `cel-python` version supports `string(map)` and `lowerAscii()`. Unverified.

---

## Readiness summary

| # | Item | Beta or scope | Readiness | What's built | What's missing |
|---|---|---|---|---|---|
| A1 | Agent memory | Beta | partial | `memory.py`, offline tests, commit claims FEVM remember and recall | Recorded cross-process run; SDK signature check |
| A2 | Databricks Sandbox | Beta, AWS only | partial | `sandbox.py`, offline tests, commit claims run and isolation | Live run output; signature check |
| A3 | Budgets | Account admin | partial | `budget.py` body builder, offline tests | Apply step; 10 unsourced fields and claims |
| A4 | Managed coding-agent config (`ug`) | Beta preview | partial | Draft JSON and README | Preview enabled; publish; Opus and Haiku check; placeholders |
| A5 | Smart Routing | Beta | not built | Nothing (plan Task 7) | Preview; session run; routing query |
| A6 | Skills on Databricks | Beta | not built | Nothing (plan Task 10) | Skill; registration; a load in the dashboard |
| A7 | Unified trace table | Beta | not built | Nothing | Enabled on demo workspace; metastore-admin question |
| A8 | Behavior evals | Opt-in | partial | Harness; offline structure and corpus tests | Any workspace run. No scores allowed |
| A9 | Contextual policies (CEL) | Managed Omnigent | not built | Nothing (plan Task 8) | Expression tests; policy file; demo |

**Ready: none.** Closest to ready: A1 and A2. Each has code, offline tests, and a commit claim. Each needs one recorded run before it's a slide.

---

## Facts to add

| Claim | Quote / detail | URL | Status |
|---|---|---|---|
| Budget body fields (unsourced) | `BUDGET_RESOURCE_TYPE_UNITY_AI_GATEWAY`, `ALERT_CONFIGURATION_SCOPE_TYPE_PER_USER`, `CUMULATIVE_SPENDING_EXCEEDED`, `BLOCK_USAGE`, `EMAIL_NOTIFICATION`, `principal_overrides`, `workspace_id` `IN` filter. Built in `src/omnigent_talk/budget.py`, no docs source | budgets API doc, to be found | OPEN |
| Budget per-model limit (unsourced) | "A budget can't be narrowed to one model service (services carry no tags)" | demos/model-services/README.md (no source) | OPEN |
| Budget apply command (unsourced) | `databricks account budgets create --json @file --profile <account-profile>`; profile needs `account_id` and `workspace_id` | budget.py docstring (no source) | OPEN |
| Sandbox create signature | Code passes `sandbox=Sandbox()` and `sandbox_id=`. Facts row shows `create_sandbox(sandbox_id=...)` only | src/omnigent_talk/sandbox.py vs facts "Sandbox SDK" | OPEN |
| Sandbox home contents (unsourced) | "Ships with `.claude`, `.codex`, `.omnigent`, `.databrickscfg`" | demos/model-services/README.md (no source) | OPEN |
| Memory SDK calls | `memory_stores.create(name, description=)` takes a display name; `search()` returns `MemorySearchResult(memory=Memory(content=...))` | demos/model-services/README.md ("SDK facts that differ from the docs") | verified in the repo README against the installed SDK; re-check on the Beta SDK version before the talk |
| Memory cross-process run | Commit `01d0ad3` says remember and recall verified on the FEVM demo workspace. No transcript and no cross-process run recorded | git commit 01d0ad3 | OPEN until a transcript exists |
| Sandbox run output | Commit `01d0ad3` says run and isolation verified. No output recorded | git commit 01d0ad3 | OPEN until a transcript exists |
| Coding-agent config probe | `GET /api/ai-gateway/v2/coding-agent-configs` on the FEVM demo workspace returns `{}` (nothing published) | todo.md; probe 2026-11-03 | verified (probe) |
| Coding-agent sync behavior (unsourced) | MCP servers and skills sync only on `ug configure`. Agent and model changes apply on relaunch | config/ug/README.md (no source) | OPEN |
| Managed config preview name | "Unity Gateway Managed Configuration", under Settings → Previews | config/ug/README.md; todo.md (no source) | OPEN |
| Usage row lag | Newest row 22 min old during the 2026-11-03 probe. Demo README says up to an hour | docs/setup-log.md §7; demos/model-services/README.md | conflicting; OPEN |
| Split demo result | `just split-demo 20` returned 16 and 4 (80/20). One run | demos/model-services/README.md | verified (one run of 20 calls) |
| Smart Routing harness coverage | Gemini and Antigravity are not routed harnesses | plan "Research Status" (no facts source yet) | OPEN; check against the Smart Routing page |
| Behavior eval corpus | 60 synthetic cases, 15 per behavior, plus a 5-case smoke set. No workspace run recorded | src/omnigent_talk/behavior_eval.py; plan Task 15 Step 5 | not run |
| Cost cap default (design, not a claim) | Non-capped users get a $100,000 threshold; the caller gets the requested cap | src/omnigent_talk/budget.py `EVERYONE_ELSE_USD` | design choice; do not present as a product limit |

---

## Gaps

- **[GAP: `talk/fallbacks/` doesn't exist.]** No clip or screenshot for any item. Each item's fallback is the narrated output, and no threshold is set yet.
- **[GAP: no numeric fallback thresholds.]** The rehearsal behavior requires one per live beat. None is set, because no beat has a timed dry run.
- **[GAP: the plan's demo directories don't exist.]** `demos/03-routing/`, `demos/04-policies/`, `demos/05-tracing/traces.md`, `demos/06-skills/`, `demos/07-memory/`, `demos/08-sandbox/`, `demos/09-collab-mobile/`, `config/omnigent/`, `config/versions.env`, `policies/`, `scripts/preflight.sh`, `talk/outline.md`, `talk/speaker-notes.md`, `talk/runbook.md`. The repo has `demos/model-services/` and `demos/routing/` instead.
- **[GAP: `lessons.md`, `tasks.md`, `checkpoint.md` don't exist.]** Plan lessons are quoted from the plan.
- **[GAP: `scripts/check.sh` runs no policy or behavior tests.]** The plan says it should, for Task 8. It doesn't yet.
- **[GAP: the bundle's destination names.]** `resources/model_services.yml` uses `models/system.ai.databricks-gemini-*` destinations. The prep reference says not to show `databricks-gemini-*` names. Setup-log probes show the services serve Gemini 3.8 Flash, so the path works. Decide how to present it before N2 is final.
- **[GAP: Qwen not probed.]** The router's Qwen destination has no served-model probe and no facts row.
- **[GAP: Opus and Haiku 5.5 not checked as served.]** The `ug` draft lists them as model services.
- **[GAP: the appendix has no runbook or timed dry run.]** Plan Task 14 isn't started.

---

## Open threads

- A3: Confirm the budgets API schema and the apply command with an account admin before any budget line goes on a slide. The per-user block also needs a decision about the default `1.00`.
- A2 and A1: Record one live run each (output, time, fallback). That's what moves them from partial to ready.
- A4: Decide whether managed config is worth a slide at all, given the preview and the admin dependency. If not, it becomes a single line in the Smart Routing slide's notes.
- A8: Decide whether behavior evals appear in the talk at all. If they do, the scores need a real run first.
- A9 and A5: Decide with the presenter whether these stay in the plan or drop out of the 45 minutes. Each is a full segment in the plan.
