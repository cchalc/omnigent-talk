-- Column-level impact for the same parameterised bakehouse object prefix.
SELECT
  max(event_time) AS last_seen,
  CASE
    WHEN entity_metadata.genie_space_id IS NOT NULL THEN 'GENIE'
    ELSE coalesce(nullif(entity_type, ''), 'DIRECT')
  END AS observed_entity_type,
  concat(source_table_schema, '.', source_table_name) AS source_object,
  source_column_name,
  concat(target_table_schema, '.', target_table_name) AS target_object,
  target_column_name,
  count(*) AS mapping_events
FROM system.access.column_lineage
WHERE event_date >= date_sub(current_date(), :lookback_days)
  AND (
    (
      source_table_catalog = coalesce(nullif(:catalog, ''), current_catalog())
      AND source_table_schema = coalesce(nullif(:schema, ''), current_schema())
      AND lower(coalesce(source_table_name, '')) LIKE 'bakehouse\_%' ESCAPE '\\'
    )
    OR (
      target_table_catalog = coalesce(nullif(:catalog, ''), current_catalog())
      AND target_table_schema = coalesce(nullif(:schema, ''), current_schema())
      AND lower(coalesce(target_table_name, '')) LIKE 'bakehouse\_%' ESCAPE '\\'
    )
  )
GROUP BY ALL
ORDER BY last_seen DESC
LIMIT 1000;
