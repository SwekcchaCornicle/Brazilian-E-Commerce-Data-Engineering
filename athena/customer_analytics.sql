-- Run after the Glue ETL job writes Parquet to the curated S3 bucket.
-- Replace <CURATED_BUCKET> and <REPORTS_BUCKET> with Terraform outputs.
-- No Glue Crawler is required: the tables below are declared with SQL.

CREATE DATABASE IF NOT EXISTS dq_platform_analytics;

-- Five Olist customer attributes plus ETL processing timestamp.
CREATE EXTERNAL TABLE IF NOT EXISTS dq_platform_analytics.customer_curated (
    customer_id STRING,
    customer_unique_id STRING,
    customer_zip_code_prefix STRING,
    customer_city STRING,
    customer_state STRING,
    processed_at TIMESTAMP
)
PARTITIONED BY (processing_date STRING)
STORED AS PARQUET
LOCATION 's3://<CURATED_BUCKET>/customer/'
TBLPROPERTIES (
    'projection.enabled' = 'true',
    'projection.processing_date.type' = 'date',
    'projection.processing_date.format' = 'yyyy-MM-dd',
    'projection.processing_date.range' = '2020-01-01,NOW',
    'projection.processing_date.interval' = '1',
    'projection.processing_date.interval.unit' = 'DAYS',
    'storage.location.template' = 's3://<CURATED_BUCKET>/customer/processing_date=${processing_date}/'
);

-- Lambda validation reports are persisted as JSON in the reports bucket.
CREATE EXTERNAL TABLE IF NOT EXISTS dq_platform_analytics.ingestion_validation_reports (
    created_at STRING,
    source STRING,
    total_records INT,
    valid_records INT,
    invalid_records INT,
    validated_output STRING,
    quarantine_output STRING,
    validation_errors ARRAY<STRUCT<record_index:INT, errors:ARRAY<STRING>>>
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
STORED AS TEXTFILE
LOCATION 's3://<REPORTS_BUCKET>/ingestion-reports/';

-- Query 1: expected one valid CUST-1001 row for the two-record demo fixture.
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state,
    processing_date
FROM dq_platform_analytics.customer_curated
WHERE customer_id = 'CUST-1001';

-- Query 2: count curated customer rows by state.
SELECT
    customer_state,
    COUNT(*) AS customer_count
FROM dq_platform_analytics.customer_curated
GROUP BY customer_state
ORDER BY customer_count DESC;

-- Query 3: aggregate Lambda validation results.
SELECT
    SUM(total_records) AS total_records,
    SUM(valid_records) AS valid_records,
    SUM(invalid_records) AS invalid_records
FROM dq_platform_analytics.ingestion_validation_reports;

-- Query 4: show source-level validation reports and output paths.
SELECT
    created_at,
    source,
    total_records,
    valid_records,
    invalid_records,
    validated_output,
    quarantine_output
FROM dq_platform_analytics.ingestion_validation_reports
ORDER BY created_at DESC
LIMIT 20;

-- Query 5: verify no required-field violations remain in curated output.
SELECT
    COUNT_IF(customer_id IS NULL OR TRIM(customer_id) = '') AS bad_customer_ids,
    COUNT_IF(customer_city IS NULL OR TRIM(customer_city) = '') AS bad_cities,
    COUNT_IF(customer_state IS NULL OR TRIM(customer_state) = '') AS bad_states
FROM dq_platform_analytics.customer_curated;
