# Query patterns

Bind `endpoint` to `$CATALOG.omnigent_talk.gemini_router`:

```sql
SELECT
  coalesce(request_tags['agent_spec'], '(unset)') AS agent_spec,
  coalesce(request_tags['harness'], '(unset)') AS harness,
  destination_model,
  count(*) AS calls,
  sum(total_tokens) AS tokens,
  sum(CASE WHEN size(routing_information.attempts) > 1 THEN 1 ELSE 0 END) AS fallbacks
FROM system.ai_gateway.usage
WHERE event_time >= date_sub(current_timestamp(), 7)
  AND requester = current_user()
  AND endpoint_name = :endpoint
GROUP BY ALL
ORDER BY calls DESC
LIMIT 100
```

Bind `prefix` to `$CATALOG.omnigent_talk.`:

```sql
SELECT DISTINCT
  source_table_full_name,
  source_type,
  target_table_full_name,
  target_type
FROM system.access.table_lineage
WHERE event_date >= date_sub(current_date(), 30)
  AND (
    startswith(source_table_full_name, concat(:prefix, 'bakehouse_'))
    OR startswith(target_table_full_name, concat(:prefix, 'bakehouse_'))
  )
LIMIT 100
```
