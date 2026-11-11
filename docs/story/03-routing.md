# 03: Traffic splits, task routing, and reading `destination_model`

Tag: workspace

## Goal

Three things, in order.

1. **A traffic split is weighted and blind to the prompt.** `gemini_router` sends 80% of calls to
   Gemini 3.8 Flash and 20% to 3.7 Flash, whatever the prompt says (`resources/model_services.yml`,
   header and `gemini_router`).
2. **Task routing happens before the gateway.** `src/omnigent_talk/router.py` asks a cheap
   classifier to label each prompt. Code and SQL go to `qwen_code`. Everything else goes to
   `gemini_general` (`router.py:1-7, 18-19`).
3. **The model that served a call is `destination_model` in `system.ai_gateway.usage`.** It is
   not the service name. The local tallies in these recipes do not always show it.

### The key lesson: the served model is `destination_model`

- A unified chat reply from a custom service echoes the service name in `model`, not the model
  that served the call (`src/omnigent_talk/gateway.py:2-5`).
- `ask` and `router-demo` print a *configured* model, taken from `SERVICE_MODELS`
  (`src/omnigent_talk/router.py:20-22, 102`). It is the model
  you configured, not evidence of what served a call.
- The served model is in `destination_model`. The same table records `routing_information.attempts`
  (fallbacks) and `request_tags` (`docs/research/facts.md`, row "Usage table columns";
  `demos/model-services/README.md:45`; `demos/routing/usage.sql:6-8`).
- Native Gemini replies carry `modelVersion`, and `split-demo` tallies that locally. So `split-demo`
  gives a result straight away, without waiting for the table (`src/omnigent_talk/routing.py:1-5,
  18-23`).
- **Rows lag, and the docs disagree on how much.** Some say about 20 minutes
  (`docs/omni-fevm.md:83`; `docs/gateway-governance.md:219`; the 2026-11-03 check saw a row
  22 minutes old, `docs/setup-log.md`, section 7). Others say up to an hour
  (`demos/model-services/README.md:48`; `demos/routing/usage.sql:2`; `demos/routing/metrics.sql:2`;
  `justfile:115`). Plan for an hour. Generate the traffic well before you show it.
- **Reading the table needs admin.** `demos/routing/usage.sql:3` says reading
  `system.ai_gateway.usage` needs account and metastore admin by default
  (`demos/model-services/README.md:93`). The facts sheet records a FEVM presenter who was a
  workspace admin and could read it (`docs/research/facts.md`, row "FEVM demo workspace"). Check
  your own access before the talk.

> **What was done.** SQL and code prompts went to Qwen, and everything else, planning and
> organizing included, went to Gemini. `gemini_router` splits its traffic between two Gemini Flash versions.

## Steps

### 1. Split: 80/20 across two Flash versions

```bash
just split-demo 20
```

This sends 20 native Gemini calls to `gemini_router` and tallies them by `modelVersion`
(`justfile:106-109`, `src/omnigent_talk/cli.py:22-31`). Each call picks a destination at random by
weight, so 20 calls give a rough split, not an exact one. The recorded run was 16 and 4, which is
80/20 (`demos/model-services/README.md:60`).

This recipe sends no session header, so it does not show session pinning. The pinning rule is in
`resources/model_services.yml` (header) and `demos/model-services/README.md:41`. Show it only if
you send a session header.

### 2. Route one prompt by task

```bash
just ask "Write a SQL query for the top 5 customers by total revenue from an orders table."
```

The recorded output was `route=sql (by gemini_fast) -> qwen_code [qwen35-122b-a10b] 4549 ms`
(`docs/setup-log.md`, section 2). `(by gemini_fast)` means the classifier answered. `(by keywords)`
means the classifier failed and the keyword rules decided (`src/omnigent_talk/router.py:83-88`).
The bracketed model is the configured one, not the served one. Use `usage-sql` in step 5 for that.

### 3. Route the demo corpus

```bash
just router-demo
```

This routes the nine prompts in `demos/routing/prompts.txt`: three code, three SQL and three
general (`demos/routing/prompts.txt:1`). Each line shows its route, and a `(keywords)` flag when
the classifier fell back (`src/omnigent_talk/cli.py:58-60`).

The classifier is `gemini_fast`, with a 256-token budget (`src/omnigent_talk/router.py:80-82`). The
budget matters: at 16 tokens the Flash Lite classifier spent everything on thinking and returned an
empty reply (`demos/model-services/README.md`, "Still open" item 5).

The keyword fallback is deliberately simple. SQL words are checked first, then code words, and
anything else is general (`src/omnigent_talk/router.py:31-36, 65-70`).

### 4. Generate traffic for the dashboard

```bash
just traffic 3 40
```

That is about 310 model calls: three rounds of 45 prompts at two calls each, plus a 40-call burst.

Three rounds of both prompt corpora (`prompts.txt` and `prompts-extended.txt`), then 40 native
calls to `gemini_router` tagged `traffic` (`justfile:175-178`). This spends model credits on the
workspace. Run it an hour or more before you show the dashboard.

### 5. Read the usage table

Wait at least an hour after the last call, then:

```bash
just usage-sql
just usage-sql "%.gemini_router"
```

`usage-sql` takes a LIKE pattern on `endpoint_name` and reads the last 24 hours. It returns the
destination model, status, number of attempts, request tags, call count and tokens
(`justfile:115-117`, `demos/routing/usage.sql`). The default pattern is `%`, which matches every
endpoint.

```bash
just routing-metrics
```

This gives calls per service, route and served model over seven days, with fallbacks and latency
(`demos/routing/metrics.sql`). The dashboard reads the same source.

### 6. Open the routing dashboard

```bash
just dashboard-url
```

This prints the URL of the dashboard that `just gateway-deploy` created (`justfile:196-198`). It
reads the bundle summary from the workspace. Viewers see the data through the publisher's access
to the usage table (`resources/dashboard.yml:7`).

## Verify

- **Split.** `just split-demo 20` gives a tally close to 80/20. The recorded run was 16 and 4
  (`demos/model-services/README.md:60`). This is a single run, not a measured distribution.
- **Route.** `just ask` on the SQL prompt prints `route=sql (by gemini_fast)` and goes to
  `qwen_code`.
- **Classifier.** The recorded classifier result was 9 of 9 prompts labelled correctly. That was
  the Flash Lite model tested directly, before deploy (`demos/model-services/README.md`, "Still open" item 5).
  It was not a `just router-demo` run on the workspace. Run `router-demo` yourself and count.
- **Served model, after the lag.** `just routing-metrics` shows `destination_model` per service.
  `gemini_router` should show both Flash versions, the SQL and code prompts should show a Qwen model,
  and the rest should show Gemini. The repo does not record the exact `destination_model` string, so read
  it from your first run rather than assuming it.

## Fallback

- **Classifier fails or returns no label.** The router uses keyword rules and tags the call
  `classifier=keywords`. `router-demo` marks it `(keywords)`. This is by design
  (`src/omnigent_talk/router.py:83-88`). Say it on stage; don't hide it.
- **Usage table is empty an hour after the traffic.** Check your access first (admin, per
  `demos/routing/usage.sql:3`). Then widen the window with `just routing-metrics`, which covers
  seven days. If rows still haven't landed, say so. The repo doesn't record a longer lag than
  about an hour.
- **Table lags on stage.** Use the local `split-demo` tally for the split, since it reads
  `modelVersion` directly (`src/omnigent_talk/routing.py:1-5`). Nothing local shows what served an
  `ask` or `router-demo` call. For those, show the table or say that you're showing configured
  routes.
- **Fallback to 3.5 Flash is not proven here.** A fallback runs only after a 429 or 5xx. The repo
  has no deterministic way to force one (`demos/model-services/README.md:42`, "Open"). Don't claim
  a fallback on stage from this chapter. If real traffic produced one, `routing_information.attempts`
  in `usage.sql` shows it.
- **Rate limiting.** `just ratelimit-demo` needs a `rate_limits` block that isn't configured. Add
  one and redeploy first (`justfile:110-112`).

Sources for this chapter: setup-log,
demo README,
gateway governance, facts.
