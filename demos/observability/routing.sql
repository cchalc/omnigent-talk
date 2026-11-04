-- gemini_router split and fallback counts. A fallback has more than one routing attempt.
SELECT
  date_trunc('HOUR', event_time) AS event_hour,
  coalesce(destination_model, '(unknown)') AS destination_model,
  count(*) AS requests,
  sum(CASE WHEN size(routing_information.attempts) > 1 THEN 1 ELSE 0 END) AS fallbacks,
  sum(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS failed_requests,
  round(avg(latency_ms)) AS avg_latency_ms,
  sum(coalesce(total_tokens, 0)) AS total_tokens
FROM system.ai_gateway.usage
WHERE event_time >= date_sub(current_date(), :lookback_days)
  AND service_type = 'MODEL_SERVICE'
  AND substring_index(endpoint_name, '.', -1) = 'gemini_router'
GROUP BY ALL
ORDER BY event_hour DESC, requests DESC
LIMIT 1000;
