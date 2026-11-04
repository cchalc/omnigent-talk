-- Token attribution is available for every Gateway request. USD by request tag is available for
-- external providers only; hosted-model spend remains visible in the built-in Usage > Spend tab.
WITH token_usage AS (
  SELECT
    CAST(event_time AS DATE) AS usage_date,
    coalesce(request_tags['agent_spec'], '(unset)') AS agent_spec,
    coalesce(request_tags['harness'], '(unset)') AS harness,
    coalesce(request_tags['demo'], '(unset)') AS demo,
    coalesce(destination_model, '(unknown)') AS destination_model,
    count(*) AS requests,
    sum(coalesce(total_tokens, 0)) AS total_tokens
  FROM system.ai_gateway.usage
  WHERE event_time >= date_sub(current_date(), :lookback_days)
  GROUP BY ALL
),
external_cost AS (
  SELECT
    usage_date,
    coalesce(custom_tags.request_tags['agent_spec'], '(unset)') AS agent_spec,
    coalesce(custom_tags.request_tags['harness'], '(unset)') AS harness,
    coalesce(custom_tags.request_tags['demo'], '(unset)') AS demo,
    coalesce(usage_metadata.model, '(unknown)') AS destination_model,
    sum(usage_quantity) AS external_cost_usd
  FROM system.ai_gateway.external_model_spend
  WHERE usage_date >= date_sub(current_date(), :lookback_days)
  GROUP BY ALL
)
SELECT
  coalesce(t.usage_date, c.usage_date) AS usage_date,
  coalesce(t.agent_spec, c.agent_spec) AS agent_spec,
  coalesce(t.harness, c.harness) AS harness,
  coalesce(t.demo, c.demo) AS demo,
  coalesce(t.destination_model, c.destination_model) AS destination_model,
  coalesce(t.requests, 0) AS requests,
  coalesce(t.total_tokens, 0) AS total_tokens,
  round(c.external_cost_usd, 6) AS external_cost_usd
FROM token_usage AS t
FULL OUTER JOIN external_cost AS c
  ON t.usage_date = c.usage_date
  AND t.agent_spec = c.agent_spec
  AND t.harness = c.harness
  AND t.demo = c.demo
  AND t.destination_model = c.destination_model
ORDER BY usage_date DESC, requests DESC;
