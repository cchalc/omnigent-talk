---
name: gateway-observability
description: Show talk routing, usage, fallback, and Bakehouse lineage from governed system tables.
---

# Gateway observability

Require `CATALOG` and `DBX_PROFILE`. Run bounded SQL with
`databricks experimental aitools tools query "$sql" --profile "$DBX_PROFILE"`, adding `--param`
for runtime names. Use the exact query patterns in `references/queries.md`.

For routing, query `system.ai_gateway.usage` over the last seven days, filter to
`requester = current_user()` and the talk's `gemini_router`, then group by
`request_tags['agent_spec']`, `request_tags['harness']`, and `destination_model`. Include calls,
tokens, and `sum(CASE WHEN size(routing_information.attempts) > 1 THEN 1 ELSE 0 END)` as fallbacks.
Pass the endpoint as a parameter resolved from `$CATALOG.omnigent_talk.gemini_router`; do not
print requester identity.

Explain that `gemini_router` is configured for an expected random 80/20 primary traffic split, so
small samples need not equal 80/20. A fallback is an extra attempt after a qualifying failure, not
part of the 80/20 allocation; the attempts array is the evidence.

For Bakehouse lineage, query `system.access.table_lineage` with a 30-day date filter. Return at
most 100 distinct source/target table pairs where either full name begins with the runtime prefix
`$CATALOG.omnigent_talk.bakehouse_`. Cite the SQL with `$CATALOG` in place of its runtime value.
