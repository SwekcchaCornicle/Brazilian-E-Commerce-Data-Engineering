-- Run in Athena after the Glue ETL job has successfully written Parquet files.
-- Replace the bucket placeholder with terraform output curated_bucket_name.
-- This table is created with SQL; no Glue Crawler is required.

CREATE DATABASE IF NOT EXISTS dq_platform_analytics;

CREATE EXTERNAL TABLE IF NOT EXISTS dq_platform_analytics.customer_curated (
    customer_id STRING,
    customer_city STRING,
    customer_state STRING,
    processed_at TIMESTAMP
)
PARTITIONED BY (
    processing_date STRING
)
STORED AS PARQUET
LOCATION 's3://<CURATED_BUCKET>/customer/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.processing_date.type' = 'date',
    'projection.processing_date.format' = 'yyyy-MM-dd',
    'projection.processing_date.range' = '2026-01-01,NOW',
    'projection.processing_date.interval' = '1',
    'projection.processing_date.interval.unit' = 'DAYS',
    'storage.location.template' = 's3://<CURATED_BUCKET>/customer/processing_date=${processing_date}/'
);

-- 1. Basic volume and distinct-customer profile.
SELECT
    processing_date,
    COUNT(*) AS customer_rows,
    COUNT(DISTINCT customer_id) AS distinct_customers
FROM dq_platform_analytics.customer_curated
GROUP BY processing_date
ORDER BY processing_date DESC;

-- 2. Customers by state.
SELECT
    customer_state,
    COUNT(*) AS customer_count
FROM dq_platform_analytics.customer_curated
GROUP BY customer_state
ORDER BY customer_count DESC
LIMIT 20;

-- 3. City-level completeness and profile.
SELECT
    customer_city,
    customer_state,
    COUNT(*) AS customer_count
FROM dq_platform_analytics.customer_curated
WHERE customer_city IS NOT NULL
  AND TRIM(customer_city) <> ''
GROUP BY customer_city, customer_state
ORDER BY customer_count DESC
LIMIT 25;

-- 4. Detect unexpected blank/null values in curated output.
SELECT
    COUNT_IF(customer_id IS NULL OR TRIM(customer_id) = '') AS bad_customer_ids,
    COUNT_IF(customer_city IS NULL OR TRIM(customer_city) = '') AS bad_cities,
    COUNT_IF(customer_state IS NULL OR TRIM(customer_state) = '') AS bad_states
FROM dq_platform_analytics.customer_curated;
