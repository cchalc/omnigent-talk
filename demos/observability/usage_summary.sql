-- One-row stage-safe KPIs. Dividing total latency by requests weights every request equally.
SELECT
  count(*) AS requests,
  sum(coalesce(total_tokens, 0)) AS total_tokens,
  round(sum(coalesce(latency_ms, 0)) / nullif(count(latency_ms), 0)) AS avg_latency_ms
FROM system.ai_gateway.usage
WHERE event_time >= date_sub(current_date(), :lookback_days)
  AND service_type = 'MODEL_SERVICE'
  AND (
    substring_index(endpoint_name, '.', -1) IN (
      'gemini_router', 'gemini_fast', 'gemini_general', 'qwen_code'
    )
    OR request_tags['demo'] = 'bakehouse'
    OR request_tags['pipeline'] = 'bakehouse'
    OR request_tags['job'] LIKE 'bakehouse-%'
  );
