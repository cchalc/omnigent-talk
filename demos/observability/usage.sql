-- Requests by request tag and destination model over time. Usage rows can lag by about one hour.
SELECT
  date_trunc('HOUR', event_time) AS event_hour,
  coalesce(request_tags['agent_spec'], '(unset)') AS agent_spec,
  coalesce(request_tags['harness'], '(unset)') AS harness,
  coalesce(request_tags['demo'], '(unset)') AS demo,
  coalesce(destination_model, '(unknown)') AS destination_model,
  count(*) AS requests,
  sum(coalesce(input_tokens, 0)) AS input_tokens,
  sum(coalesce(output_tokens, 0)) AS output_tokens,
  sum(coalesce(total_tokens, 0)) AS total_tokens,
  round(avg(latency_ms)) AS avg_latency_ms
FROM system.ai_gateway.usage
WHERE event_time >= date_sub(current_date(), :lookback_days)
GROUP BY ALL
ORDER BY event_hour DESC, requests DESC;
