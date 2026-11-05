-- Demo model-service requests by request tag and destination model over time.
SELECT
  date_trunc('HOUR', event_time) AS event_hour,
  coalesce(
    nullif(request_tags['agent_spec'], ''),
    nullif(request_tags['job'], ''),
    '(unset)'
  ) AS agent_spec,
  coalesce(
    nullif(request_tags['harness'], ''),
    nullif(session_metadata.coding_agent, ''),
    '(unset)'
  ) AS harness,
  coalesce(
    nullif(request_tags['demo'], ''),
    nullif(request_tags['pipeline'], ''),
    '(unset)'
  ) AS demo,
  coalesce(destination_model, '(unknown)') AS destination_model,
  count(*) AS requests,
  sum(coalesce(input_tokens, 0)) AS input_tokens,
  sum(coalesce(output_tokens, 0)) AS output_tokens,
  sum(coalesce(total_tokens, 0)) AS total_tokens,
  sum(coalesce(latency_ms, 0)) AS latency_ms_sum
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
  )
GROUP BY ALL
ORDER BY event_hour DESC, requests DESC
LIMIT 1000;
