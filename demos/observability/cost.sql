-- Token attribution is available for every Gateway request. USD by request tag is available for
-- external providers only; hosted-model spend remains visible in the built-in Usage > Spend tab.
WITH token_usage AS (
  SELECT
    CAST(event_time AS DATE) AS usage_date,
    coalesce(
      nullif(request_tags['harness'], ''),
      nullif(session_metadata.coding_agent, ''),
      nullif(request_tags['agent_spec'], ''),
      nullif(request_tags['job'], ''),
      '(unset)'
    ) AS harness,
    count(*) AS requests,
    sum(coalesce(total_tokens, 0)) AS total_tokens
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
),
external_cost AS (
  SELECT
    usage_date,
    coalesce(
      nullif(custom_tags.request_tags['harness'], ''),
      nullif(custom_tags.request_tags['agent_spec'], ''),
      nullif(custom_tags.request_tags['job'], ''),
      '(unset)'
    ) AS harness,
    sum(usage_quantity) AS external_cost_usd
  FROM system.ai_gateway.external_model_spend
  WHERE usage_date >= date_sub(current_date(), :lookback_days)
    AND (
      substring_index(usage_metadata.endpoint_name, '.', -1) IN (
        'gemini_router', 'gemini_fast', 'gemini_general', 'qwen_code'
      )
      OR custom_tags.request_tags['demo'] = 'bakehouse'
      OR custom_tags.request_tags['pipeline'] = 'bakehouse'
      OR custom_tags.request_tags['job'] LIKE 'bakehouse-%'
    )
  GROUP BY ALL
)
SELECT
  coalesce(t.usage_date, c.usage_date) AS usage_date,
  coalesce(t.harness, c.harness) AS harness,
  coalesce(t.requests, 0) AS requests,
  coalesce(t.total_tokens, 0) AS total_tokens,
  round(c.external_cost_usd, 6) AS external_cost_usd
FROM token_usage AS t
FULL OUTER JOIN external_cost AS c
  ON t.usage_date = c.usage_date
  AND t.harness = c.harness
ORDER BY usage_date DESC, requests DESC
LIMIT 1000;
