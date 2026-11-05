-- Smart Routing decisions that reached this workspace's Unity Gateway: one row per router, agent
-- and served model. Calls a harness sends to another gateway (an org-pinned Claude or Codex)
-- land in that gateway's table instead. Rows can take up to an hour to arrive.
SELECT
  session_metadata.smart_router_name AS smart_router,
  session_metadata.coding_agent AS coding_agent,
  destination_model,
  count(*) AS calls,
  count(DISTINCT session_metadata.client_session_id) AS sessions,
  sum(total_tokens) AS tokens,
  min(event_time) AS first_call,
  max(event_time) AS last_call
FROM system.ai_gateway.usage
WHERE session_metadata.smart_router_name IS NOT NULL
  AND requester = current_user()
  AND event_time >= date_sub(current_date(), 7)
GROUP BY ALL
ORDER BY calls DESC
