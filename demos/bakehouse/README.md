# Bakehouse analytics: metric views, an AI/BI dashboard and a Genie agent

What this demo shows: governed data on the same workspace the agents use. PII-free copies of
`samples.bakehouse`, review sentiment scored by **Gemini** in SQL (`ai_query`), two **metric
views** that hold each KPI definition once, and the dashboard and **Genie agent** built on them.
Everything comes from one isolated bundle in `analytics/` and runs through `just`. The profile,
catalog and schema come from `.env.local`.

## What gets built

All objects land in `<catalog>.<schema>`, the schema the gateway bundle owns (default
`omnigent_talk`), next to the model services.

| Object | Built by | Contents |
| :---- | :---- | :---- |
| `bakehouse_transactions` | job, `sql/01_copy_tables.sql` | 3,333 sales. `cardNumber` dropped |
| `bakehouse_customers` | job, `sql/01_copy_tables.sql` | 300 customers, location and gender only. Names, email, phone, street address and postal code dropped |
| `bakehouse_franchises` | job, `sql/01_copy_tables.sql` | 48 stores. 21 point at a supplier that isn't in the sample |
| `bakehouse_suppliers` | job, `sql/01_copy_tables.sql` | 27 suppliers, one ingredient each |
| `bakehouse_reviews` | job, `sql/01_copy_tables.sql` | 204 reviews |
| `bakehouse_review_sentiment` | job, `sql/02_review_sentiment.sql` | Successful Gemini scores only: one row per review with a valid label (positive, negative, mixed, neutral) and a one-line summary |
| `bakehouse_review_sentiment_errors` | job, `sql/02_review_sentiment.sql` | Reviews whose latest scoring call failed or returned no valid label. Empty after a clean run |
| `bakehouse_sales_metrics` | job, `sql/03_metric_views.sql` | Metric view: Total Revenue, Units Sold, Transaction Count, Unique Customers, Average Transaction Value, Avg Units per Transaction, Revenue per Customer, by day/month, product, payment method, franchise name/city/country/size, customer country/continent, supplier name/ingredient (`Unknown` when the supplier is missing) |
| `bakehouse_review_metrics` | job, `sql/03_metric_views.sql` | Metric view over successfully scored reviews only: Review Count, Avg Review Length, Positive/Negative/Mixed/Neutral Reviews, Positive Share, by franchise, city, country, sentiment and day |
| *omnigent-talk: Bakehouse sales and sentiment* | bundle dashboard | KPIs, daily revenue, product mix, top 10 franchises, payment mix, sentiment by city |
| *omnigent-talk: Bakehouse analyst* | bundle Genie space | The 2 metric views and 6 tables, 10 sample questions, 1 instruction, 2 example SQLs |
| *omnigent-talk: bakehouse build* | bundle job | The three SQL files above, in order, on the Serverless Starter Warehouse |

Every table and column has a comment, and every metric-view dimension and measure has a
comment and synonyms. Genie and the catalog UI read these.

## Deploy, run, redeploy

```bash
just analytics-validate   # bundle validate --strict
just analytics-deploy     # job, dashboard and Genie agent
just analytics-run        # builds the tables, sentiment and metric views (about 40 s)
```

On a clean schema, run `analytics-deploy` and then `analytics-run`. The dashboard and Genie
agent deploy before their tables exist and show data once the job has run. To redeploy after a
change, repeat `analytics-deploy` (it reports `0 changed` when nothing changed), and re-run the
job if you changed any SQL. The job is re-run safe: copies and metric views are
`CREATE OR REPLACE`, and sentiment only calls the model for reviews without a successful score.
Reviews already scored are never sent again. Failed calls and invalid labels never reach
`bakehouse_review_sentiment` or the metrics. They are listed in
`bakehouse_review_sentiment_errors` and retried on the next run. A re-run makes no model calls
only when every review is already scored.

`just analytics-destroy` removes the job, dashboard and Genie agent. It can't drop the schema
or the model services, because this bundle doesn't declare the schema. The tables and metric
views stay too, because the job's SQL created them, not the bundle.

## Sentiment path: Foundation Model API, not the Unity Gateway service

The goal was to score reviews through the Unity Gateway service `<catalog>.<schema>.gemini_general`
with `ai_query`. On the demo workspace that fails at compile time:

```
[AI_FUNCTION_COMPILATION_ERROR] ... INVALID_ARGUMENT: ai_query through UC Model Services is not enabled.
```

The same error comes back for the `model-services/<catalog>.<schema>.gemini_general` form (both
probed 2026-11-03). So the live path is the pay-per-token Foundation Model API endpoint
`databricks-gemini-3-8-flash`, the same model `gemini_general` routes to. It's called with a JSON
schema response format, so each answer is one of positive, negative, mixed or neutral. The first
run scored all 204 reviews with no row errors: 106 positive, 88 negative, 10 mixed.

The endpoint is the bundle variable `sentiment_endpoint`, passed to the SQL as a job parameter.
To switch once ai_query on UC Model Services is enabled:

```bash
export BUNDLE_VAR_sentiment_endpoint="$CATALOG.$SCHEMA.gemini_general"
just analytics-deploy
# then empty bakehouse_review_sentiment (or delete the rows to re-score) and run:
just analytics-run
```

## What to show on stage

- **Lineage** (Catalog Explorer, *Lineage* tab on `bakehouse_sales_metrics` or
  `bakehouse_review_metrics`): `samples.bakehouse.*` -> `bakehouse_*` tables -> metric view, with
  the build job on the edges. Checked through the lineage API after the first run. The
  dashboard and Genie agent did **not** appear as downstream entities at that point. Open the
  graph before the talk, and only claim the dashboard/Genie edge if it shows up.
- **Metric views:** one definition per KPI. The dashboard widgets and Genie's SQL both call
  `MEASURE(...)` on the same view. Asked "What are the top 5 franchises by revenue?", Genie wrote
  ``MEASURE(`Total Revenue`)`` against `bakehouse_sales_metrics`.
- **Gemini in SQL:** `bakehouse_review_sentiment` and the *sentiment by city* chart.
- **Unity Gateway:** don't say the sentiment calls went through Unity Gateway. They went to
  the Foundation Model API endpoint, so they won't appear under `gemini_general` in the routing
  dashboard. The gateway story stays with the router and agy demos
  (`demos/model-services/README.md`). Where the sentiment calls are recorded hasn't been
  checked.

Before anything here goes on a slide, add the claim and its source to
`docs/research/facts.md`.
