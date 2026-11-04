-- Bakehouse agent calls over the last day, by agent and harness, with the model that served
-- each one. agy and Claude Code tag `agent_spec`/`harness`; Codex and pi carry Omnigent's CI
-- keys (`job` = agent), and their harness comes from the coding-agent header.
-- Usage rows land within about an hour. Reading the table needs account and metastore admin.
SELECT
  coalesce(request_tags['agent_spec'], request_tags['job'], '(untagged)') AS agent,
  coalesce(request_tags['harness'], session_metadata.coding_agent, '-') AS harness,
  endpoint_name,
  destination_model,
  status_code,
  count(*) AS calls,
  sum(total_tokens) AS tokens
FROM system.ai_gateway.usage
WHERE event_time > now() - INTERVAL 24 HOURS
  AND requester = current_user()
  AND (request_tags['demo'] = 'bakehouse' OR request_tags['pipeline'] = 'bakehouse')
GROUP BY ALL
ORDER BY agent, calls DESC;
