# Unity Gateway model services, agy, agent memory, and Sandbox

What this demo shows: a **custom model service** on Unity Gateway (traffic split, fallback,
rate limit, budget) that Antigravity (agy) uses for its Gemini calls, plus **managed agent
memory** and **Databricks Sandbox** on the same workspace. Everything runs from `just`; settings
come from `.env.local`.

## Setup

```bash
cp .env.example .env.local   # fill in DBX_PROFILE, CATALOG, SCHEMA, SHIM_PORT, SHIM_KEY, ...
just install
just check
```

## Model services (bundle: `databricks.yml`, `resources/`)

| Service | Routing |
| :---- | :---- |
| `gemini_router` | 80% Gemini 3.8 Flash, 20% Gemini 3.7 Flash; fallback to 3.5 Flash on 429/5xx. agy's main turns |
| `gemini_fast` | 100% Gemini 3.1 Flash Lite. The router's classifier and agy's background calls |
| `gemini_general` | 100% Gemini 3.8 Flash. Router target for general prompts |
| `qwen_code` | 100% Qwen 3.5 122B. Router target for coding and SQL (unified chat API only; agy can't use it) |

No service has a rate limit right now.

```bash
just gateway-deploy          # schema + services (DABs `model_services`, Beta)
just gateway-show            # destinations, fallback, rate limit
just probe                   # one native Gemini call: the go/no-go for agy
just split-demo 20           # tally of the model that served each call (≈80/20)
just ratelimit-demo 60       # burst past the limit, count the 429s
just ask "Write a SQL query for the top 5 customers by revenue"   # -> sql -> qwen_code
just router-demo             # 9 prompts (3 code, 3 SQL, 3 general) and a tally of routes
just routing-metrics         # per service / route / served model, from system.ai_gateway.usage
just dashboard-url           # the routing dashboard (deployed with the bundle)
just gateway-destroy
```

What the docs support, and how each one is shown:
- **Traffic splitting:** up to 5 destinations whose percentages sum to 100. Requests are routed at random, and requests with a session header stick to one destination (session affinity). Shown with `split-demo`, which tallies `modelVersion` locally so there's no wait.
- **Fallbacks:** destinations are tried in order on 429/5xx. Fallbacks have no traffic split. The retries appear in `routing_information.attempts` in the usage table. **Open:** a deterministic way to force a failure (see below).
- **Rate limits:** per-user or per-service QPM/TPM, returning HTTP 429. Not configured right now; add a `rate_limits` block and redeploy before `ratelimit-demo`.
- **Budgets:** account-level, with resource type *Unity Gateway*, per-user thresholds, and alert or **block usage** actions. A budget can only be narrowed to a workspace, not to a service (services carry no tags). On a shared workspace a per-user block would stop everyone, so `just budget 0.50` blocks **only you**: everyone else gets a $100,000 threshold, and a principal override sets yours to $0.50. `--alert-only` emails you instead of blocking. `--everyone` applies the cap to all users; don't use it on a shared workspace. An account admin applies the printed body with `databricks account budgets create --json @budget.json --profile <account-profile>`.
- **How a service decides:** it never reads the prompt. It picks a destination at random by weight on every request, keeps a session on one destination when a session header is sent, and moves to the fallback only after a 429 or 5xx. Every decision is in `system.ai_gateway.usage`: `destination_model`, and `routing_information.attempts[]` (`INITIAL_ATTEMPT` vs. fallback, each with status and latency).
- **Routing by task happens before the gateway.** `src/omnigent_talk/router.py` asks `gemini_fast` to label each prompt `code`, `sql` or `general` (keywords decide if that call fails), then sends code and SQL to `qwen_code` and the rest to `gemini_general`. Both calls carry request tags (`demo=router`, `stage=classify|answer`, `route=…`), so the usage table and the dashboard show each decision next to the model that served it. agy does a client-side version of the same thing: its background `*-lite` calls go to `gemini_fast` and its turns to `gemini_router` (the shim's `--lite`). Say plainly on the slide that this routing is client-side.
- **Served model:** native Gemini replies name it (`modelVersion`). Unified chat replies from a custom service only echo the service name, so `ask` shows the *configured* model of the single-destination service, and the true `destination_model` comes from the usage table.
- **Dashboard** (`dashboards/routing.lvdash.json`, deployed by the bundle on the Serverless Starter Warehouse): calls, share served by Qwen, average latency, fallbacks; which model served each service; router route → model; calls per minute; recent calls. Usage rows can take **up to an hour** to land, so run the traffic well before you show it.

## agy on a custom service

Omnigent's agy adapter only discovers `system.ai.gemini-*` services
(`omnigent/models/databricks_model_discovery.py`), so `omni agy` can't target
`<catalog>.<schema>.gemini_router` directly. `src/omnigent_talk/gemini_shim.py` is a small
localhost proxy that adds the profile's Databricks auth and pins the target service.

- **Bare agy:** `just agy -p "…"` runs agy with an isolated `--gemini_dir` whose settings select API-key auth (`modelProvider: gemini`). Without that setting agy ignores `GEMINI_API_KEY` and uses its Google login. Its base URL env var is `GOOGLE_GEMINI_BASE_URL`.
- **Through Omnigent:** `omni agy --server …` launches agy from the host daemon, so env vars from your shell never reach it. Instead, run `just agy-serve` (fixed `SHIM_PORT` and `SHIM_KEY`), then add the provider that `just agy-provider` prints to your Omnigent config, and make it the gemini default in place of `databricks-gemini-fevm-cjc`. Omnigent's bridge sets `modelProvider: gemini` itself whenever a key provider is in use (read from source, not yet run end to end).

**Go/no-go passed (2026-11-03):** after `just gateway-deploy`, both custom services list `gemini/v1/generateContent` in `supported_api_types`, and `just probe` returns 200 (`gemini_router` was served by `gemini-3.8-flash`, `gemini_fast` by `gemini-3.1-flash-lite`). `just split-demo 20` came out 16/4 (80/20). `just agy -p "Reply with exactly: pong"` ran with its turn on `gemini_router` and its lite call on `gemini_fast`. `just agy` runs in the directory you call it from, which becomes agy's workspace.

Earlier checks, using system services as the target:
- `agy -p` went through the shim and answered.
- agy requested `gemini-3.1-pro-preview` for its turn and `gemini-3.1-flash-lite-preview` for background work.
- `--lite` routed the two requests to different services.

## Agent memory (managed, Lakebase-backed, Beta)

```bash
just memory-create                       # finds the store by display name, creates it if missing
just remember "prefers Gemini" presenter
just recall "which model?" presenter     # new process, recalls the fact
just recall "which model?" someone-else  # nothing
```

Creating a store provisions its Lakebase storage, so there is no Lakebase project to set up; you pay for the Lakebase underneath. `actor_id` scopes what gets recalled, but it is **not** access control. SDK facts that differ from the docs (`databricks-agentbricks` 0.8.0, import `databricks_agentkit`):
- `memory_stores.create(display_name, description=)` takes a display name. Store ids are assigned by the server.
- `search()` returns `MemorySearchResult(memory=Memory(content=…), score=…)`.

## Databricks Sandbox (Beta)

```bash
just sandbox-run "python3 -c 'print(sum(range(10)))'"   # 45, then the sandbox is deleted
just sandbox-isolation                                    # home=/home/sandbox-agent
```

Ingress is closed, and the sandbox has its own filesystem and identity. **Egress is unrestricted**, so don't claim network isolation. The sandbox home ships with `.claude`, `.codex`, `.omnigent` and `.databrickscfg` already in place.

## Still open

1. **Forced fallback.** Options: make the primary destination a `model_provider_services` CUSTOM provider pointed at an endpoint that always returns 5xx, or show the logged retry attempts from real traffic.
2. **Budget apply.** Needs an account-level profile for this account and account admin rights.
3. **Usage table access.** Reading `system.ai_gateway.usage` needs account and metastore admin by default.
4. **`omni agy` on the custom service.** Run `just agy-serve` and add the provider entry from `just agy-provider`. Not run end to end yet.
5. **Router quality.** On 2026-11-03, the Flash Lite classifier labelled all 9 demo prompts correctly (tested against `system.ai.gemini-3-1-flash-lite` before deploy). Its budget is 256 tokens: with 16, Flash Lite spent everything on thinking and replied empty.
