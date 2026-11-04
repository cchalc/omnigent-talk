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
| `gemini_router` | 80% Gemini 3.8 Flash, 20% Gemini 3.7 Flash; fallback to 3.5 Flash on 429/5xx; per-user requests-per-minute limit (`REQUESTS_PER_MINUTE` in `.env.local`, default 30) |
| `gemini_fast` | 100% Gemini 3.1 Flash Lite. The cheap tier |

```bash
just gateway-deploy          # schema + services (DABs `model_services`, Beta)
just gateway-show            # destinations, fallback, rate limit
just probe                   # one native Gemini call: the go/no-go for agy
just split-demo 20           # tally of the model that served each call (≈80/20)
just ratelimit-demo 60       # burst past the limit, count the 429s
just usage-sql 'gemini_%'    # the same traffic in system.ai_gateway.usage (≈1 h delay)
just gateway-destroy
```

What the docs support, and how each one is shown:
- **Traffic splitting:** up to 5 destinations whose percentages sum to 100. Requests are routed at random, and requests with a session header stick to one destination (session affinity). Shown with `split-demo`, which tallies `modelVersion` locally so there's no wait.
- **Fallbacks:** destinations are tried in order on 429/5xx. Fallbacks have no traffic split. The retries appear in `routing_information.attempts` in the usage table. **Open:** a deterministic way to force a failure (see below).
- **Rate limits:** per-user or per-service QPM/TPM, returning HTTP 429. Shown with `ratelimit-demo`.
- **Budgets:** account-level, with resource type *Unity Gateway*, per-user thresholds, and alert or **block usage** actions. A budget can only be narrowed to a workspace, not to a service (services carry no tags). On a shared workspace a per-user block would stop everyone, so `just budget 0.50` blocks **only you**: everyone else gets a $100,000 threshold, and a principal override sets yours to $0.50. `--alert-only` emails you instead of blocking. `--everyone` applies the cap to all users; don't use it on a shared workspace. An account admin applies the printed body with `databricks account budgets create --json @budget.json --profile <account-profile>`.
- **"Custom routing":** Unity Gateway documents no rule-based routing. The routing in this demo is client-side tiering: agy's background `*-lite` calls go to `gemini_fast`, and its turns go to `gemini_router` (the shim's `--lite`). Say this plainly on the slide.

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
5. **Rate limit vs agy.** At 30 requests per minute, a live agy segment can hit 429s. Set `REQUESTS_PER_MINUTE` higher and redeploy for that segment.
