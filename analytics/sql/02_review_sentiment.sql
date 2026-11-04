-- Scores each review's sentiment with Gemini through ai_query, once per review.
-- Re-run safe and cheap: only reviews without a score are sent to the model, so a re-run after a
-- full success makes no model calls. Failed rows are dropped and retried on the next run.
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
  error_message STRING COMMENT 'ai_query error for this row, if any (the row is retried next run)',
  scored_at TIMESTAMP COMMENT 'When the score was produced'
)
COMMENT 'Gemini sentiment for each bakehouse review, produced by ai_query in the bakehouse_build job.';

DELETE FROM bakehouse_review_sentiment
WHERE sentiment IS NULL
   OR review_id NOT IN (SELECT review_id FROM bakehouse_reviews);

INSERT INTO bakehouse_review_sentiment
SELECT
  review_id,
  franchise_id,
  review_date,
  length(review) AS review_length,
  lower(parsed.sentiment) AS sentiment,
  parsed.summary AS summary,
  {{sentiment_endpoint}} AS model_endpoint,
  ai.errorMessage AS error_message,
  current_timestamp() AS scored_at
FROM (
  SELECT *, from_json(ai.result, 'sentiment STRING, summary STRING') AS parsed
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
) AS scored;
