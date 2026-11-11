# 02: Model services as a bundle, then a native Gemini probe

Tag: workspace

## Goal

Deploy the Unity Gateway model services as a Databricks Asset Bundle, check what the gateway
now serves, and send one native Gemini call. That call is the go/no-go for pointing agy at a
custom service.

The bundle is `databricks.yml` plus `resources/`:

- `databricks.yml` names the bundle, includes `resources/*.yml`, defines the `catalog` and
  `schema` variables, and sets the `dev` target. The catalog and schema come from `.env.local`
  through `just`, so nothing workspace-specific is committed (`databricks.yml:1-24`).
- `resources/schema.yml` makes the schema a bundle resource. Its comment says the schema holds
  the model services and inference tables (`resources/schema.yml:1-6`).
- `resources/model_services.yml` defines four services: `gemini_router`, `gemini_fast`,
  `gemini_general` and `qwen_code`. Its header states the rule the rest of this story depends
  on: a service never reads the prompt. With several destinations it picks one at random by
  `traffic_percentage` on each request. A session header pins a session to one destination.
  Fallbacks run in order only after a 429 or 5xx (`resources/model_services.yml:1-7`).
- `resources/dashboard.yml` deploys the routing dashboard from `dashboards/routing.lvdash.json`
  on the Serverless Starter Warehouse, which the bundle looks up by name rather than by ID
  (`databricks.yml:14-18`, `resources/dashboard.yml:1-7`).

Model services are Beta in DABs (`resources/model_services.yml:1`).

### Three API surfaces in `gateway.py`

`src/omnigent_talk/gateway.py` talks to the gateway in three ways:

1. **Native Gemini.** `GEMINI_ROUTE` is `/ai-gateway/gemini/v1beta/models`. `GeminiGateway.generate`
   posts a Gemini-shaped body to `<service>:generateContent` (`gateway.py:21, 43-44, 117-122`).
   The reply carries `modelVersion`, which is the only place a service call says which model
   answered (`gateway.py:70-72`). This is the surface agy speaks, and the one the go/no-go tests.
2. **Unified chat.** `CHAT_ROUTE` is `/ai-gateway/mlflow/v1/chat/completions`. `GeminiGateway.chat`
   posts OpenAI-style messages with `model` set to the service name (`gateway.py:22, 124-137`).
   Chat works for any model, but on a custom service the reply's `model` only echoes the service
   name, so the served model does not appear there (`gateway.py:2-5`).
3. **The tags header.** `Databricks-Ai-Gateway-Request-Tags` carries a JSON map (`gateway.py:23,
   113-114`). It is a request header, not an API. It is how the router's decisions (`demo`,
   `stage`, `route`, `classifier`) reach `request_tags` in `system.ai_gateway.usage`
   (`src/omnigent_talk/router.py:79, 99`). Chapter 03 uses this.

### Why native Gemini cannot serve a service that mixes in Qwen

Native Gemini answers are Gemini-shaped and name a Gemini `modelVersion`. Qwen speaks only the
unified chat and responses APIs, not native Gemini. The bundle says so next to `qwen_code`
(`resources/model_services.yml`, comment above `qwen_code`), and the demo README repeats it
(`demos/model-services/README.md:23`). A Qwen destination therefore cannot answer a
`generateContent` call. agy needs the native API: the facts sheet records that native Gemini is
required and that OpenAI Responses and Chat Completions are not supported for agy
(`docs/research/facts.md`, row "Native agy creds").

That is why the repo keeps `qwen_code` as its own service, and sends code and SQL to it from the
client (`src/omnigent_talk/router.py:1-7`), rather than putting Qwen inside `gemini_router`.

**Not verified:** no run in this repo sent a native Gemini call to a service with a Qwen
destination, so the repo does not record the exact failure. The reasoning above is inference
from the Qwen comment and the native-only agy path.

## Steps

### 1. Validate and plan (no change)

```bash
just gateway-validate
just gateway-plan
```

`validate` runs `databricks bundle validate --strict --target dev`. `plan` lists what a deploy
would create, change and delete, without deploying (`justfile:51-59`). Both reach the workspace
named by `$DBX_PROFILE`.

The last recorded plan (2026-11-03) was: create `dashboards.routing`, `gemini_general` and
`qwen_code`; update `gemini_router` and `gemini_fast` (`docs/setup-log.md`, section 2). Run the
plan again. The bundle on your branch may not match that run.

### 2. State the blast radius, get confirmation, then deploy

Before `just gateway-deploy`, say three things to the presenter: the target (`dev`), the profile
(`$DBX_PROFILE`), and the blast radius from the plan. Get an explicit yes. The 2026-11-03 deploy
had a blast radius that mattered: the update to `gemini_router` dropped its per-user rate limit
(`docs/setup-log.md`, section 2, commit `5a630a7`).

```bash
just gateway-deploy
```

Recorded result: `Resources: 3 created, 2 changed, 0 deleted` (`docs/setup-log.md`, section 2).

### 3. Check what the gateway now serves

```bash
just gateway-show gemini_router
just gateway-show qwen_code
```

`gateway-show` prints each service's name, `config` and `supported_api_types` (`justfile:97-100`).
For `gemini_router` you should see two destinations at 80 and 20 (plus a fallback), and no rate limit. After a
deploy, `gemini_router` and `gemini_fast` should both list `gemini/v1/generateContent` in
`supported_api_types` (`demos/model-services/README.md:60`).

### 4. Probe native Gemini: the go/no-go for agy

```bash
just probe
just probe gemini_fast
```

The probe makes one native `generateContent` call and prints one line:
`<service>: HTTP <status> model=<modelVersion> text=...`. It exits 0 only on HTTP 200
(`src/omnigent_talk/cli.py:13-19`).

The passing bar is HTTP 200 (the `model=` value can be empty). The recorded run (2026-11-03) reported
`gemini_router` served by `gemini-3.8-flash` and `gemini_fast` by `gemini-3.1-flash-lite`
(`demos/model-services/README.md:60`). `gemini_router` splits 80/20, so one probe can land on
3.7 Flash. A single 3.7 answer is not a failure.

### 5. Point agy at a custom service through the shim

Omnigent's agy adapter only discovers `system.ai.gemini-*` services, so `omni agy` cannot target
`<catalog>.<schema>.gemini_router` directly. `src/omnigent_talk/gemini_shim.py` is a localhost
proxy that adds the profile's Databricks auth and pins the target service
(`demos/model-services/README.md:52-53`, `src/omnigent_talk/gemini_shim.py:1-14`).

Bare agy, through the shim:

```bash
just agy -p "Reply with exactly: pong"
```

Run it from the directory you want agy to use as its workspace (`justfile:126-130`). Agy's turns
go to `gemini_router`, and its background `*-lite` calls go to `gemini_fast`. The recorded run
did this (`demos/model-services/README.md:60`).

Through Omnigent, run the shim as a server, then print the provider entry:

```bash
just agy-serve
just agy-provider
```

`agy-serve` listens on `SHIM_PORT` with the key `SHIM_KEY` (`src/omnigent_talk/cli.py:78-80`).
`agy-provider` only prints a YAML block. Add it to your Omnigent config yourself, substituting your own `SHIM_KEY` for the placeholder in the
printed block. Don't commit the result. Only one
provider can be the gemini default, so unset the other one first (`justfile:136-139`). The repo
never edits `~/.omnigent`; recipes print config for the presenter to apply.

**Set up, not run end to end:** `omni agy` on the custom service. The shim and provider block are
in place; the bridge behavior was read from source, not tested (`demos/model-services/README.md:58`, "Still open" item 4).

### 6. Print the budget body; an account admin applies it

```bash
just budget 0.50 > "$HOME/budget-omnigent-talk.json"
```

The recipe looks up your user in the workspace and fails with "The profile needs account_id and
workspace_id set" if the profile lacks them (`src/omnigent_talk/cli.py:121-124`). The account budgets
API is in Public Preview.

Keep the file outside the repo; the repo is public. The recipe creates nothing, but it does call
the workspace to look up your user ID (`src/omnigent_talk/cli.py:127`). The body sets a monthly
per-user cap that blocks Unity Gateway usage. It blocks only you: everyone else gets a $100,000
threshold, and your override is $0.50 (`src/omnigent_talk/budget.py:18-19, 44-49`). The
`--alert-only` flag emails you instead of blocking. `--everyone` applies the cap to all users,
so don't use it on a shared workspace (`justfile:119-122`).

An account admin applies the file, with an account-level profile:

```bash
databricks account budgets create --json @"$HOME/budget-omnigent-talk.json" --profile <account-profile>
```

Budgets are account-level, and a budget can only be narrowed to a workspace, not to one model
service (`src/omnigent_talk/budget.py:1-11`). The facts sheet records that account admins set
budgets and rate limits (`docs/research/facts.md`, row "Budgets / rate limits").

### 7. Tear down (only with confirmation)

```bash
just gateway-plan
just gateway-destroy
```

`destroy` deletes everything the bundle created (`justfile:65-67`). The schema is a bundle
resource too (`resources/schema.yml`), and its comment says it holds the inference tables. Read
the delete list from the plan before you confirm. The repo does not record whether destroy
removes table data.

## Verify

- `just gateway-show gemini_router` shows two destinations at 80 and 20, and no rate limit.
- `just probe` prints `HTTP 200` with a `model=` value, and exits 0.
- `just agy -p "Reply with exactly: pong"` answers. Its turn should show on `gemini_router` in the
  usage table once rows land (chapter 03).
- The story's own checks pass, with no workspace needed:

```bash
uv run pytest tests/test_story.py -k "02-gateway or 03-routing"
```

## Fallback

- **Validate or plan fails.** Stop. Don't deploy. Fix the error and run `just gateway-validate`
  again.
- **Deploy fails partway.** Don't retry blindly, and don't destroy as a fix. Run
  `just gateway-plan` and read it. The repo does not record how a partial deploy recovers.
- **Probe returns non-200.** Run `just gateway-show <service>`. If `supported_api_types` does not
  list `gemini/v1/generateContent`, the service has no native route, so fix the service rather
  than the client. A 403 that says a legacy Gemini endpoint "is no longer available. Use Unity
  Catalog model services" means the call used a retired name. Use `system.ai.gemini-*` instead
  (`docs/research/facts.md`, row "Legacy Gemini endpoints retired").
- **agy won't go through the shim.** Skip the custom services. The Databricks provider with
  `native_gemini: true` and a `system.ai.gemini-*` model worked for agy, and the setup log
  switched to Gemini 3.8 Flash inside agy (`docs/setup-log.md`, sections 4 and 6). The demo
  then doesn't show the traffic split, so say so on stage.
- **No Databricks access.** This chapter can't be replayed. Keep the offline checks in the
  Verify section, which need no credentials.

Sources for this chapter: setup-log,
demo README,
facts, gateway governance.
