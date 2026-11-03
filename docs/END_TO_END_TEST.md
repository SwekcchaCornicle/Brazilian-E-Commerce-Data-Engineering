# End-to-end test runbook: five-field customer example

This runbook demonstrates one small two-record JSON file flowing through the platform. The example uses five customer attributes aligned with the Olist customer dataset. It is a **synthetic test fixture**, not a copied Kaggle customer record.

## 1. The five-field input

File: [`terraform/customers_5_fields_e2e.json`](../terraform/customers_5_fields_e2e.json)

```json
[
  {
    "customer_id": "  CUST-1001  ",
    "customer_unique_id": "UNQ-9001",
    "customer_zip_code_prefix": "01001",
    "customer_city": "  sao paulo  ",
    "customer_state": " sp "
  },
  {
    "customer_id": "CUST-1002",
    "customer_unique_id": "UNQ-9002",
    "customer_zip_code_prefix": "20010",
    "customer_city": "",
    "customer_state": "rj"
  }
]
```

Expected Lambda result for this file: 2 total records, 1 valid record, 1 invalid record. Lambda requires `customer_id`, `customer_city`, and `customer_state`; the other two Olist customer fields are preserved and carried through when present.

## 2. Get the deployed bucket names

From the Terraform directory:

```cmd
terraform output
terraform output -raw curated_bucket_name
terraform output -raw reports_bucket_name
```

The development deployment used AWS region `us-west-2` and CLI profile `admin`. The suffixes in your deployment may differ if you create a new workspace/account.

## 3. Upload the input file to Raw S3

Run from the Terraform directory:

```cmd
aws s3 cp customers_5_fields_e2e.json s3://<RAW_BUCKET>/e2e/customers_5_fields_e2e.json --profile admin --region us-west-2
```

The S3 Object Created event flows through EventBridge to the SQS ingestion queue, which triggers Lambda.

## 4. Lambda validation: Validated S3, Quarantine S3, and report

Lambda checks the three required fields. It preserves the five customer attributes in the records.

Expected **validated** JSON Lines record:

```json
{"customer_id":"  CUST-1001  ","customer_unique_id":"UNQ-9001","customer_zip_code_prefix":"01001","customer_city":"  sao paulo  ","customer_state":" sp "}
```

Expected **quarantine** JSON Lines record:

```json
{"record_index":1,"record":{"customer_id":"CUST-1002","customer_unique_id":"UNQ-9002","customer_zip_code_prefix":"20010","customer_city":"","customer_state":"rj"},"errors":["Empty required field: customer_city"]}
```

The Lambda also writes an ingestion validation report to:

```text
s3://<REPORTS_BUCKET>/ingestion-reports/<timestamp>/customers_5_fields_e2e.json.report.json
```

Example report content:

```json
{
  "created_at": "2026-11-04T00:00:00+00:00",
  "source": "s3://<RAW_BUCKET>/e2e/customers_5_fields_e2e.json",
  "total_records": 2,
  "valid_records": 1,
  "invalid_records": 1,
  "validated_output": "s3://<VALIDATED_BUCKET>/processed/<timestamp>/customers_5_fields_e2e.json",
  "quarantine_output": "s3://<QUARANTINE_BUCKET>/quarantine/<timestamp>/customers_5_fields_e2e.json",
  "validation_errors": [
    {
      "record_index": 1,
      "errors": ["Empty required field: customer_city"]
    }
  ]
}
```

The timestamp and bucket suffixes above are illustrative. The report written at runtime contains the real values.

Verify the three output areas:

```cmd
aws s3 ls s3://<VALIDATED_BUCKET>/processed/ --recursive --profile admin --region us-west-2
aws s3 ls s3://<QUARANTINE_BUCKET>/quarantine/ --recursive --profile admin --region us-west-2
aws s3 ls s3://<REPORTS_BUCKET>/ingestion-reports/ --recursive --profile admin --region us-west-2
```

Download and inspect a report:

```cmd
aws s3 cp s3://<REPORTS_BUCKET>/<REPORT_KEY> validation_report.json --profile admin --region us-west-2
type validation_report.json
```

Lambda also logs the per-object counts to CloudWatch. The report object is the persistent S3 record; CloudWatch is operational logging.

## 5. Glue ETL: read the same validated data, not quarantine

The Glue job reads only:

```text
s3://<VALIDATED_BUCKET>/processed/
```

It does **not** read the quarantine prefix. The script uses Spark's default JSON Lines reader; Lambda writes each validated record as one JSON object per line.

For the valid sample, Glue applies:

| Field | Before ETL | After ETL |
|---|---|---|
| `customer_id` | `"  CUST-1001  "` | `"CUST-1001"` |
| `customer_unique_id` | `"UNQ-9001"` | `"UNQ-9001"` |
| `customer_zip_code_prefix` | `"01001"` | `"01001"` |
| `customer_city` | `"  sao paulo  "` | `"sao paulo"` |
| `customer_state` | `" sp "` | `"SP"` |

The zip prefix stays a string so leading zeroes are preserved. Glue adds `processed_at` and `processing_date`, then writes Parquet under:

```text
s3://<CURATED_BUCKET>/customer/processing_date=YYYY-MM-DD/
```

The blank-city record has already been rejected by Lambda. Glue performs a second required-field check on validated input as a defensive quality check.

## 6. Run and verify the Glue job

The Lambda code, environment, and IAM policy were updated to add the S3 validation report. The Glue script was updated to use five customer fields and read JSON Lines. Apply the Terraform changes after reviewing the plan:

```cmd
terraform fmt
terraform validate
terraform plan -out=e2e-update.tfplan
terraform show -no-color e2e-update.tfplan
```

Review the Lambda code hash, Lambda environment variable `REPORTS_BUCKET`, Lambda report-prefix permission, Glue script object upload, and Glue job configuration. Do not apply if the plan contains unexpected destroys or unrelated changes.

```cmd
terraform apply e2e-update.tfplan
```

Confirm and start the Glue job:

```cmd
aws glue get-job --job-name dq-platform-customer-etl --profile admin --region us-west-2
aws glue start-job-run --job-name dq-platform-customer-etl --profile admin --region us-west-2
```

Copy the returned JobRunId and poll:

```cmd
aws glue get-job-run --job-name dq-platform-customer-etl --run-id <JOB_RUN_ID> --query "JobRun.JobRunState" --output text --profile admin --region us-west-2
```

Expected: `SUCCEEDED`. If it fails, inspect `ErrorMessage`, `LogGroupName`, and the CloudWatch logs. Verify Parquet objects:

```cmd
aws s3 ls s3://<CURATED_BUCKET>/customer/ --recursive --profile admin --region us-west-2
```

A Terraform-created job is not proof of a successful execution; record the actual JobRunId and state.

## 7. Query the curated Parquet data using Athena

The SQL is in [`athena/customer_analytics.sql`](../athena/customer_analytics.sql). Get the bucket values:

```cmd
terraform output -raw curated_bucket_name
terraform output -raw reports_bucket_name
```

Replace `<CURATED_BUCKET>` and `<REPORTS_BUCKET>` in the SQL, open Athena in `us-west-2`, and configure an Athena query-results S3 location. Run the DDL statements first, then the SELECT statements.

Example query:

```sql
SELECT
    customer_state,
    COUNT(*) AS customer_count
FROM dq_platform_analytics.customer_curated
GROUP BY customer_state
ORDER BY customer_count DESC;
```

For the two-record fixture, the expected *illustrative* result after Lambda and Glue is:

| customer_state | customer_count |
|---|---:|
| SP | 1 |

The second record has a blank city and is quarantined, so it never reaches curated Parquet. The actual Athena grid may include other rows if other customer objects are already present under the validated prefix.

Query the ingestion validation report itself:

```sql
SELECT
    SUM(total_records) AS total_records,
    SUM(valid_records) AS valid_records,
    SUM(invalid_records) AS invalid_records
FROM dq_platform_analytics.ingestion_validation_reports;
```

For this fixture alone, expected illustrative counts are 2 total, 1 valid, 1 invalid. When the reports table contains other runs, totals will be higher.

Save the Athena query execution ID and an actual result screenshot for the project's runtime evidence. Do not present illustrative values as captured AWS output.

## 8. Optional Glue Crawler

The optional resource is in `terraform/glue_crawler_optional.tf` and is disabled by default. In the development account, `CreateCrawler` returned:

```text
AccessDeniedException: Account 553607360155 is denied access.
```

Only after AWS confirms access is available, enable it using:

```cmd
terraform plan -var="enable_glue_crawler=true"
terraform apply -var="enable_glue_crawler=true"
```

The direct-S3 ETL and explicit Athena DDL in this runbook work without a crawler.

## 9. Completion checklist

- [x] S3 data zones and event-driven ingestion infrastructure deployed.
- [x] Valid customer happy-path fixture processed and validated output observed.
- [x] Schema evolution comparison report generated and stored in S3.
- [x] Curated S3 bucket deployed with versioning and AES256 encryption.
- [x] Five-field sample, S3 validation-report code, Glue ETL update, Athena SQL, and documentation committed.
- [ ] Apply and verify the updated Lambda report/JSON-Lines behavior in AWS.
- [ ] Verify this fixture creates one validated row, one quarantine row, and one S3 validation report.
- [ ] Run Glue ETL and confirm `SUCCEEDED`.
- [ ] Confirm the Parquet file exists and contains all five customer fields.
- [ ] Execute Athena queries and save actual result evidence.
- [ ] Enable optional crawler only if the account restriction is lifted.

The sample fixture is synthetic and is intended to explain the pipeline. The full source data is the Olist Kaggle dataset, linked and attributed in [`docs/DATA_SOURCE.md`](DATA_SOURCE.md).
