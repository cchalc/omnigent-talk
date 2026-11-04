-- Coding-agent calls by session over the last 7 days, from the Unity Gateway usage table.
-- session_metadata is only populated for coding-agent traffic. The table is account-wide, so
-- this keeps your own rows. Rows can take up to an hour to land.
SELECT
  coalesce(session_metadata.coding_agent, '-') AS coding_agent,
  coalesce(session_metadata.surface, '-') AS surface,
  coalesce(session_metadata.client_session_id, '-') AS client_session_id,
  endpoint_name AS endpoint_or_service,
  destination_model,
  count(*) AS calls,
  sum(total_tokens) AS tokens,
  min(event_time) AS first_event,
  max(event_time) AS last_event
FROM system.ai_gateway.usage
WHERE event_time >= date_sub(current_date(), 7)
  AND requester = current_user()
  AND session_metadata.coding_agent IS NOT NULL
GROUP BY ALL
ORDER BY last_event DESC
