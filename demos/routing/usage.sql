-- Routing for the demo services over the last day: which destination served each call,
-- and whether a fallback fired. Usage rows land within about an hour.
-- Reading system.ai_gateway.usage needs account and metastore admin by default.
SELECT
  endpoint_name,
  destination_model,
  status_code,
  size(routing_information.attempts) AS attempts,
  request_tags,
  count(*) AS calls,
  sum(total_tokens) AS tokens
FROM system.ai_gateway.usage
WHERE event_time > now() - INTERVAL 24 HOURS
  AND endpoint_name LIKE :service_pattern
GROUP BY ALL
ORDER BY calls DESC;
