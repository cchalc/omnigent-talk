-- Which model served each demo service, by router route, over the last 7 days.
-- Same source as the routing dashboard. Rows can take up to an hour to land.
SELECT
  substring_index(endpoint_name, '.', -1) AS service,
  coalesce(request_tags['route'], '-') AS route,
  destination_model,
  count(*) AS calls,
  sum(CASE WHEN size(routing_information.attempts) > 1 THEN 1 ELSE 0 END) AS fallbacks,
  round(avg(latency_ms)) AS avg_latency_ms,
  round(percentile(latency_ms, 0.95)) AS p95_latency_ms,
  sum(total_tokens) AS tokens
FROM system.ai_gateway.usage
WHERE endpoint_name LIKE '%.omnigent_talk.%'
  AND event_time >= date_sub(current_date(), 7)
GROUP BY ALL
ORDER BY service, route, calls DESC
