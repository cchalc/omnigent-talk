-- Copies samples.bakehouse into the demo schema with snake_case names and no PII.
-- Re-run safe: every statement replaces a table or its comments. The comments feed Genie and
-- the catalog UI.
-- {{catalog}} and {{schema}} are job parameters (see resources/bakehouse_build.job.yml).

USE CATALOG IDENTIFIER({{catalog}});
USE SCHEMA IDENTIFIER({{schema}});

-- cardNumber is dropped: it is a payment card number.
CREATE OR REPLACE TABLE bakehouse_transactions
COMMENT 'Bakehouse point-of-sale transactions, one row per sale. Copied from samples.bakehouse.sales_transactions without the card number.'
AS SELECT
  transactionID AS transaction_id,
  customerID AS customer_id,
  franchiseID AS franchise_id,
  dateTime AS transaction_ts,
  product,
  quantity,
  unitPrice AS unit_price,
  totalPrice AS total_price,
  paymentMethod AS payment_method
FROM samples.bakehouse.sales_transactions;

ALTER TABLE bakehouse_transactions ALTER COLUMN
  transaction_id COMMENT 'Unique sale id (primary key)',
  customer_id COMMENT 'Buyer; joins bakehouse_customers.customer_id',
  franchise_id COMMENT 'Selling store; joins bakehouse_franchises.franchise_id',
  transaction_ts COMMENT 'When the sale happened (UTC)',
  product COMMENT 'Bakehouse product sold, for example Pearly Pies',
  quantity COMMENT 'Units sold in this transaction',
  unit_price COMMENT 'Price of one unit, in US dollars',
  total_price COMMENT 'quantity * unit_price, in US dollars (the revenue of the sale)',
  payment_method COMMENT 'Card network used: amex, mastercard or visa';

-- Names, email, phone, street address and postal code are dropped.
CREATE OR REPLACE TABLE bakehouse_customers
COMMENT 'Bakehouse customers with location only. Copied from samples.bakehouse.sales_customers without names, email, phone, address or postal code.'
AS SELECT
  customerID AS customer_id,
  city,
  state,
  country,
  continent,
  gender
FROM samples.bakehouse.sales_customers;

ALTER TABLE bakehouse_customers ALTER COLUMN
  customer_id COMMENT 'Unique customer id (primary key)',
  city COMMENT 'Customer home city',
  state COMMENT 'Customer home state or region',
  country COMMENT 'Customer home country',
  continent COMMENT 'Customer home continent',
  gender COMMENT 'Customer gender as recorded in the sample data';

CREATE OR REPLACE TABLE bakehouse_franchises
COMMENT 'Bakehouse franchise stores. Copied from samples.bakehouse.sales_franchises.'
AS SELECT
  franchiseID AS franchise_id,
  name AS franchise_name,
  city,
  district,
  zipcode,
  country,
  size,
  longitude,
  latitude,
  supplierID AS supplier_id
FROM samples.bakehouse.sales_franchises;

ALTER TABLE bakehouse_franchises ALTER COLUMN
  franchise_id COMMENT 'Unique store id (primary key)',
  franchise_name COMMENT 'Store name; not unique on its own, so pair it with city',
  city COMMENT 'Store city',
  district COMMENT 'Store district',
  zipcode COMMENT 'Store postal code',
  country COMMENT 'Store country',
  size COMMENT 'Store size band: S, M, L, XL or XXL',
  longitude COMMENT 'Store longitude',
  latitude COMMENT 'Store latitude',
  supplier_id COMMENT 'Main ingredient supplier; joins bakehouse_suppliers.supplier_id. 21 of 48 stores reference a supplier that is not in the sample';

CREATE OR REPLACE TABLE bakehouse_suppliers
COMMENT 'Bakehouse ingredient suppliers. Copied from samples.bakehouse.sales_suppliers.'
AS SELECT
  supplierID AS supplier_id,
  name AS supplier_name,
  ingredient,
  continent,
  city,
  district,
  size,
  longitude,
  latitude,
  approved
FROM samples.bakehouse.sales_suppliers;

ALTER TABLE bakehouse_suppliers ALTER COLUMN
  supplier_id COMMENT 'Unique supplier id (primary key)',
  supplier_name COMMENT 'Supplier name',
  ingredient COMMENT 'The one ingredient this supplier provides, for example cacao',
  continent COMMENT 'Supplier continent',
  city COMMENT 'Supplier city',
  district COMMENT 'Supplier district',
  size COMMENT 'Supplier size band',
  longitude COMMENT 'Supplier longitude',
  latitude COMMENT 'Supplier latitude',
  approved COMMENT 'Whether the supplier is approved (Y/N)';

CREATE OR REPLACE TABLE bakehouse_reviews
COMMENT 'Customer reviews of bakehouse stores. Copied from samples.bakehouse.media_customer_reviews.'
AS SELECT
  new_id AS review_id,
  franchiseID AS franchise_id,
  review_date,
  review
FROM samples.bakehouse.media_customer_reviews;

ALTER TABLE bakehouse_reviews ALTER COLUMN
  review_id COMMENT 'Unique review id (primary key)',
  franchise_id COMMENT 'Reviewed store; joins bakehouse_franchises.franchise_id',
  review_date COMMENT 'When the review was posted (UTC)',
  review COMMENT 'Free-text customer review';
