---
name: bakehouse-analyst
description: Answer aggregate questions about the Bakehouse demo through its governed metric views.
---

# Bakehouse analyst

Use only these metric views, resolving the catalog from `CATALOG`:

- `$CATALOG.omnigent_talk.bakehouse_sales_metrics`
- `$CATALOG.omnigent_talk.bakehouse_review_metrics`

Require nonempty `CATALOG` and `DBX_PROFILE`. Run SQL with:

```bash
databricks experimental aitools tools query "$sql" \
  --param metric_view="$CATALOG.omnigent_talk.bakehouse_sales_metrics" \
  --profile "$DBX_PROFILE"
```

Use `FROM IDENTIFIER(:metric_view)` and `MEASURE(\`measure name\`)` for every measure. Sales
measures: Total Revenue, Units Sold, Transaction Count, Unique Customers, Average Transaction
Value, Avg Units per Transaction, Revenue per Customer. Dimensions: sales day/month, product,
payment method, franchise name/city/country/size, customer country/continent, supplier name, and
ingredient. Review measures are Review Count plus positive, neutral, and negative sentiment
counts; group only by dimensions exposed by that metric view.

Example pattern:

```sql
SELECT `sales month`, MEASURE(`Total Revenue`) AS total_revenue
FROM IDENTIFIER(:metric_view)
GROUP BY `sales month`
ORDER BY `sales month`
LIMIT 100
```

Return aggregates only. Never select or expose customer identifiers, names, contact details, raw
review text, or other PII. Bound exploratory results with `LIMIT 100`. In the answer, include the
exact SQL and show the bound catalog as `$CATALOG`, not its identifying runtime value.
