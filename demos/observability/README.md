# Unity Gateway observability demo

This is a screen-safe, five-minute path through Unity Gateway usage, routing, tracing, and
lineage. Run `just obs-usage`, `just obs-routing`, and `just obs-lineage` before rehearsal. The
queries are read-only, date-bounded, and capped at 1,000 result rows; the one-row KPI query is
aggregate-only. `system.ai_gateway.usage` can lag live calls by about one hour.

## Router verification (2026-11-03)

- `gemini_router`: the native Gemini probe returned HTTP 200. Ten calls split 7 to Gemini 3.8
  Flash and 3 to Gemini 3.7 Flash; the service also has Gemini 3.5 Flash configured as its ordered
  fallback.
- `gemini_fast`: 9/9 router-demo classifications succeeded without keyword fallback.
- `gemini_general`: 3/3 general router-demo prompts succeeded on Gemini 3.8 Flash.
- `qwen_code`: 6/6 code and SQL router-demo prompts succeeded on Qwen.

Reproduce from the repository root:

```bash
just gateway-show gemini_router
just gateway-show gemini_fast
just gateway-show gemini_general
just gateway-show qwen_code
just probe gemini_router
just split-demo 10
just router-demo
```

The SQL function `ai_query('system.ai.gemini-3-8-flash', ...)` returned a response. An earlier
read-only SQL probe also observed the legacy `databricks-gemini-3-8-flash` alias working, but use
the `system.ai.*` name on stage because legacy endpoint behavior is not the talk contract. The
custom UC service call failed with `AI_FUNCTION_COMPILATION_ERROR`: current Unity Gateway
`ai_query` support is limited to Databricks-provided `system.ai.*` services, not user-created UC
model services. See [Query foundation and embedding models](https://docs.databricks.com/gcp/en/ai-gateway/query-model-services).

## Stage path

1. Open **Unity Gateway > Usage**. Start on Overview, then use Coding Agents and Spend to show
   governed request metadata, model/token usage, and platform-calculated spend. Request tags
   `agent_spec`, `harness`, `demo`, `pipeline`, and `job` connect a harness decision to its
   destination model. The assets include only the four demo model services or requests tagged for
   bakehouse, so unrelated account traffic does not dominate the stage view. If the latest live
   calls are absent, use the deployed dashboard or terminal query and explain the ingestion lag.
2. Open the **Routing split** dashboard page. `gemini_router` is a weighted 80/20 service, so a
   small sample need not land exactly at 80/20. A fallback is counted only when
   `routing_information.attempts` contains more than one attempt. If usage has not landed, use the
   immediate local tally from `just split-demo 10`.
3. Open **Unity Gateway > Govern > Traces** and label the unified trace table **Beta**. This
   workspace did not expose a trace table in the configured demo schema during setup. A metastore
   admin must select **Set up tracing**, choose a Unity Catalog catalog/schema/table, save it, and
   grant the presenter `SELECT`. Then query that chosen table by `trace_id` to reconstruct its
   OpenTelemetry spans. If it is still unavailable, show Usage and say that tracing setup is the
   missing prerequisite rather than implying that no calls occurred.
4. Open the **Lineage** dashboard page, then the Catalog Explorer lineage view for a bakehouse
   object. The SQL treats rows with `entity_metadata.genie_space_id` as Genie because the lineage
   table does not use a `GENIE` `entity_type`; jobs and AI/BI dashboards appear as `JOB` and
   `DASHBOARD_V3`.
5. In Catalog Explorer, select a model service and open its lineage. The complete service lineage
   story is **foundation model -> model service -> inference table**. The first edge comes from the
   service's configured destination; the second appears only after an inference table is attached
   and receives traffic. If the second edge is absent, show the service configuration and the
   table-lineage dashboard instead of claiming it exists.

## Cost boundary

`cost.sql` aggregates request-tagged tokens and USD estimates to day and harness before joining,
so provider-model naming differences cannot split the two sides. USD comes from
`system.ai_gateway.external_model_spend`. That USD field covers external providers only. Hosted
model cost does not retain per-request harness tags in the billing table, so use Unity Gateway's
built-in Spend tab for hosted-model cost rather than inventing a token price.

## Sources

- [Usage tracking and built-in dashboard](https://docs.databricks.com/gcp/en/ai-gateway/usage-tracking)
- [Cost observability](https://docs.databricks.com/gcp/en/ai-gateway/cost-observability)
- [Unified trace table (Beta)](https://docs.databricks.com/gcp/en/ai-gateway/unified-trace-table)
- [Unity Catalog lineage system tables](https://docs.databricks.com/gcp/en/admin/system-tables/lineage)
- [Model provider services and inference tables](https://docs.databricks.com/gcp/en/ai-gateway/model-provider-services)
