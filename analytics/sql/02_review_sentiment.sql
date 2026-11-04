-- Scores each review's sentiment with Gemini through ai_query, once per review.
-- Only successful scores with a valid label reach bakehouse_review_sentiment. Failures go to
-- bakehouse_review_sentiment_errors and are retried on the next run, because a review counts as
-- scored only once it has a row in bakehouse_review_sentiment. Re-run safe: a run after a full
-- success makes no model calls.
-- {{sentiment_endpoint}} is a job parameter; see demos/bakehouse/README.md for why it is the
-- Foundation Model API endpoint rather than the Unity Gateway service gemini_general.

USE CATALOG IDENTIFIER({{catalog}});
USE SCHEMA IDENTIFIER({{schema}});

CREATE TABLE IF NOT EXISTS bakehouse_review_sentiment (
  review_id INT COMMENT 'Scored review; joins bakehouse_reviews.review_id',
  franchise_id BIGINT COMMENT 'Reviewed store; joins bakehouse_franchises.franchise_id',
  review_date TIMESTAMP COMMENT 'When the review was posted (UTC)',
  review_length INT COMMENT 'Length of the review text, in characters',
  sentiment STRING COMMENT 'Overall sentiment from Gemini: positive, negative, mixed or neutral',
  summary STRING COMMENT 'One-sentence Gemini summary of the review',
  model_endpoint STRING COMMENT 'Serving endpoint that produced the score',
  scored_at TIMESTAMP COMMENT 'When the score was produced'
)
COMMENT 'Successful Gemini sentiment scores, one per bakehouse review, produced by ai_query in the bakehouse_build job. Failed calls are in bakehouse_review_sentiment_errors.'
TBLPROPERTIES ('delta.columnMapping.mode' = 'name');

-- The first version of this table stored failures too, in an error_message column. Drop the
-- column and any row that is not a valid score, so only successes remain.
ALTER TABLE bakehouse_review_sentiment SET TBLPROPERTIES ('delta.columnMapping.mode' = 'name');
ALTER TABLE bakehouse_review_sentiment DROP COLUMN IF EXISTS error_message;

DELETE FROM bakehouse_review_sentiment
WHERE sentiment IS NULL
   OR sentiment NOT IN ('positive', 'negative', 'neutral', 'mixed')
   OR review_id NOT IN (SELECT review_id FROM bakehouse_reviews);

-- Call the model once per unscored review and keep the result, so the success and failure
-- inserts below read the same answers instead of calling the model twice.
CREATE OR REPLACE TABLE bakehouse_review_sentiment_attempts
COMMENT 'Scratch table for one bakehouse_build run: each unscored review and its ai_query result. Dropped at the end of the run.'
AS SELECT
  review_id,
  franchise_id,
  review_date,
  review_length,
  sentiment,
  summary,
  model_endpoint,
  error_message,
  raw_result,
  coalesce(error_message IS NULL AND sentiment IN ('positive', 'negative', 'neutral', 'mixed'), false)
    AS is_scored,
  attempted_at
FROM (
  SELECT
    review_id,
    franchise_id,
    review_date,
    length(review) AS review_length,
    lower(trim(from_json(ai.result, 'sentiment STRING, summary STRING').sentiment)) AS sentiment,
    from_json(ai.result, 'sentiment STRING, summary STRING').summary AS summary,
    {{sentiment_endpoint}} AS model_endpoint,
    ai.errorMessage AS error_message,
    ai.result AS raw_result,
    current_timestamp() AS attempted_at
  FROM (
    SELECT
      r.review_id,
      r.franchise_id,
      r.review_date,
      r.review,
      ai_query(
        {{sentiment_endpoint}},
        concat(
          'Classify the overall sentiment of this bakery customer review as positive, ',
          'negative, mixed or neutral, and summarise it in one sentence. Review: ',
          r.review
        ),
        responseFormat => '{"type":"json_schema","json_schema":{"name":"review_sentiment","strict":true,"schema":{"type":"object","properties":{"sentiment":{"type":"string","enum":["positive","negative","mixed","neutral"]},"summary":{"type":"string"}},"required":["sentiment","summary"]}}}',
        failOnError => false
      ) AS ai
    FROM bakehouse_reviews r
    LEFT ANTI JOIN bakehouse_review_sentiment s ON s.review_id = r.review_id
  ) AS called
) AS parsed;

INSERT INTO bakehouse_review_sentiment (
  review_id, franchise_id, review_date, review_length, sentiment, summary, model_endpoint, scored_at
)
SELECT
  review_id, franchise_id, review_date, review_length, sentiment, summary, model_endpoint,
  attempted_at
FROM bakehouse_review_sentiment_attempts
WHERE is_scored;

-- Failures from the latest run only: an earlier failure that has since scored is gone.
CREATE OR REPLACE TABLE bakehouse_review_sentiment_errors
COMMENT 'Reviews whose latest ai_query sentiment call failed or returned no valid label. Retried on the next bakehouse_build run.'
AS SELECT
  review_id,
  franchise_id,
  review_date,
  model_endpoint,
  error_message,
  raw_result,
  attempted_at
FROM bakehouse_review_sentiment_attempts
WHERE NOT is_scored;

DROP TABLE IF EXISTS bakehouse_review_sentiment_attempts;
