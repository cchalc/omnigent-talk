-- Governed bakehouse metrics: one definition each, shared by the dashboard and the Genie agent.
-- Re-run safe: CREATE OR REPLACE. Sources are unqualified, so they resolve in the catalog and
-- schema chosen by the USE statements below ({{catalog}} and {{schema}} are job parameters).
-- The SQL task splits statements before it parses $$ bodies: keep apostrophes and semicolons out
-- of the YAML text.

USE CATALOG IDENTIFIER({{catalog}});
USE SCHEMA IDENTIFIER({{schema}});

CREATE OR REPLACE VIEW bakehouse_sales_metrics
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: >-
  Bakehouse sales KPIs over bakehouse_transactions, sliceable by day, product, payment method,
  store, customer location and the ingredient supplier of the store. Revenue is in US dollars.
source: bakehouse_transactions
joins:
  - name: dim_franchise
    source: bakehouse_franchises
    'on': source.franchise_id = dim_franchise.franchise_id
    joins:
      - name: dim_supplier
        source: bakehouse_suppliers
        'on': dim_franchise.supplier_id = dim_supplier.supplier_id
  - name: dim_customer
    source: bakehouse_customers
    'on': source.customer_id = dim_customer.customer_id
dimensions:
  - name: Sales Day
    expr: "DATE_TRUNC('DAY', source.transaction_ts)"
    comment: Calendar day of the sale (UTC)
    synonyms: [day, date, sale date]
  - name: Sales Month
    expr: "DATE_TRUNC('MONTH', source.transaction_ts)"
    comment: Calendar month of the sale (UTC)
    synonyms: [month]
  - name: Product
    expr: source.product
    comment: Bakehouse product sold
    synonyms: [item, cookie, pastry]
  - name: Payment Method
    expr: source.payment_method
    comment: Card network used to pay (amex, mastercard, visa)
    synonyms: [card, card type, payment type]
  - name: Franchise Name
    expr: dim_franchise.franchise_name
    comment: Store name. Not unique, so pair with Franchise City
    synonyms: [store, franchise, shop]
  - name: Franchise City
    expr: dim_franchise.city
    comment: City of the selling store
    synonyms: [store city, city]
  - name: Franchise Country
    expr: dim_franchise.country
    comment: Country of the selling store
    synonyms: [store country, market]
  - name: Franchise Size
    expr: dim_franchise.size
    comment: Store size band (S, M, L, XL, XXL)
    synonyms: [store size, size]
  - name: Customer Country
    expr: dim_customer.country
    comment: Home country of the buyer
    synonyms: [buyer country]
  - name: Customer Continent
    expr: dim_customer.continent
    comment: Home continent of the buyer
    synonyms: [buyer continent, region]
  - name: Supplier Name
    expr: "COALESCE(dim_franchise.dim_supplier.supplier_name, 'Unknown')"
    comment: Ingredient supplier of the selling store. Unknown when the supplier is not in the sample
    synonyms: [supplier, vendor]
  - name: Supplier Ingredient
    expr: "COALESCE(dim_franchise.dim_supplier.ingredient, 'Unknown')"
    comment: Ingredient that supplier provides. Unknown when the supplier is not in the sample
    synonyms: [ingredient]
measures:
  - name: Total Revenue
    expr: SUM(source.total_price)
    comment: Sum of total_price, in US dollars
    synonyms: [revenue, sales, turnover]
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: max
        places: 0
  - name: Units Sold
    expr: SUM(source.quantity)
    comment: Total units sold
    synonyms: [units, quantity, volume]
  - name: Transaction Count
    expr: COUNT(1)
    comment: Number of sales
    synonyms: [transactions, orders, sales count]
  - name: Unique Customers
    expr: COUNT(DISTINCT source.customer_id)
    comment: Distinct buyers
    synonyms: [customers, buyers]
  - name: Average Transaction Value
    expr: "MEASURE(`Total Revenue`) / MEASURE(`Transaction Count`)"
    comment: Revenue per sale, in US dollars
    synonyms: [ATV, average order value, AOV, basket size]
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: max
        places: 2
  - name: Avg Units per Transaction
    expr: "MEASURE(`Units Sold`) / MEASURE(`Transaction Count`)"
    comment: Units per sale
    synonyms: [units per order]
  - name: Revenue per Customer
    expr: "MEASURE(`Total Revenue`) / MEASURE(`Unique Customers`)"
    comment: Revenue per distinct buyer, in US dollars
    synonyms: [spend per customer]
    format:
      type: currency
      currency_code: USD
      decimal_places:
        type: max
        places: 2
$$;

CREATE OR REPLACE VIEW bakehouse_review_metrics
WITH METRICS
LANGUAGE YAML
AS $$
version: 1.1
comment: >-
  Bakehouse review KPIs over bakehouse_review_sentiment (Gemini-scored), sliceable by store,
  city, sentiment and day.
source: bakehouse_review_sentiment
joins:
  - name: dim_franchise
    source: bakehouse_franchises
    'on': source.franchise_id = dim_franchise.franchise_id
dimensions:
  - name: Review Day
    expr: "DATE_TRUNC('DAY', source.review_date)"
    comment: Calendar day the review was posted (UTC)
    synonyms: [day, date]
  - name: Sentiment
    expr: source.sentiment
    comment: Gemini sentiment of the review (positive, negative, mixed, neutral)
    synonyms: [tone, feeling]
  - name: Franchise Name
    expr: dim_franchise.franchise_name
    comment: Reviewed store name. Not unique, so pair with Franchise City
    synonyms: [store, franchise, shop]
  - name: Franchise City
    expr: dim_franchise.city
    comment: City of the reviewed store
    synonyms: [city, store city]
  - name: Franchise Country
    expr: dim_franchise.country
    comment: Country of the reviewed store
    synonyms: [country, market]
measures:
  - name: Review Count
    expr: COUNT(1)
    comment: Number of reviews
    synonyms: [reviews, number of reviews]
  - name: Avg Review Length
    expr: AVG(source.review_length)
    comment: Mean review length, in characters
    synonyms: [average review length]
  - name: Positive Reviews
    expr: "COUNT(1) FILTER (WHERE source.sentiment = 'positive')"
    comment: Reviews Gemini scored positive
    synonyms: [positive count]
  - name: Negative Reviews
    expr: "COUNT(1) FILTER (WHERE source.sentiment = 'negative')"
    comment: Reviews Gemini scored negative
    synonyms: [negative count, complaints]
  - name: Mixed Reviews
    expr: "COUNT(1) FILTER (WHERE source.sentiment = 'mixed')"
    comment: Reviews Gemini scored mixed
    synonyms: [mixed count]
  - name: Positive Share
    expr: "MEASURE(`Positive Reviews`) / MEASURE(`Review Count`)"
    comment: Fraction of reviews scored positive (0 to 1)
    synonyms: [positive rate, satisfaction]
    format:
      type: percentage
      decimal_places:
        type: max
        places: 1
$$;
