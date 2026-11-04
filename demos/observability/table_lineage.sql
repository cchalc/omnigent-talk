-- Bakehouse table lineage, including jobs, AI/BI dashboards and Genie-originated queries.
SELECT
  event_time,
  CASE
    WHEN entity_metadata.genie_space_id IS NOT NULL THEN 'GENIE'
    ELSE coalesce(entity_type, 'DIRECT')
  END AS observed_entity_type,
  source_table_full_name,
  source_type,
  target_table_full_name,
  target_type,
  direct_access
FROM system.access.table_lineage
WHERE event_date >= date_sub(current_date(), :lookback_days)
  AND (
    lower(coalesce(source_table_full_name, '')) LIKE
      lower(concat(:catalog, '.', :schema, '.bakehouse', chr(95), '%'))
    OR lower(coalesce(target_table_full_name, '')) LIKE
      lower(concat(:catalog, '.', :schema, '.bakehouse', chr(95), '%'))
  )
ORDER BY event_time DESC
LIMIT 1000;
