# End-to-end test runbook

This runbook documents the expected execution sequence. It distinguishes tests already reported during development from steps that still require a successful live AWS run.

## Environment

The development deployment used:
- AWS region: `us-west-2`
- AWS CLI profile: `admin`
- Terraform-managed S3 zones, EventBridge, SQS, Lambda, and Glue resources.

Get the actual bucket names from Terraform outputs; do not assume suffixes in another account:

```cmd
cd /d C:\Users\singh\OneDrive\Desktop\schema-evalution\terraform
terraform output
```

## 1. Valid and invalid ingestion fixtures

Upload valid fixture:

```cmd
aws s3 cp valid_customer.json s3://<RAW_BUCKET>/e2e/valid_customer.json --profile admin --region us-west-2
```

Upload invalid fixture:

```cmd
aws s3 cp invalid_customer.json s3://<RAW_BUCKET>/e2e/invalid_customer.json --profile admin --region us-west-2
```

Inspect validated and quarantine zones:

```cmd
aws s3 ls s3://<VALIDATED_BUCKET>/processed/ --recursive --profile admin --region us-west-2
aws s3 ls s3://<QUARANTINE_BUCKET>/quarantine/ --recursive --profile admin --region us-west-2
```

Inspect Lambda logs:

```cmd
aws logs describe-log-streams --log-group-name /aws/lambda/dq-platform-ingestion --order-by LastEventTime --descending --max-items 5 --profile admin --region us-west-2
```

Expected: valid fixture appears in validated output; invalid fixture appears in quarantine output with validation errors. Confirm the actual object paths and log counts rather than relying on upload success alone.

## 2. Schema evolution

From the Terraform directory:

```cmd
python -m py_compile advanced_schema_evolution.py
python advanced_schema_evolution.py
python schema_registry_service.py
```

Expected example for customer schema v2 → v3: `customer_city` is removed and `customer_segment` becomes required; the comparison classifies the change as incompatible under the current structural rules. Confirm the generated JSON report in the reports bucket.

## 3. Glue ETL job

Confirm the job exists:

```cmd
aws glue get-job --job-name dq-platform-customer-etl --profile admin --region us-west-2
```

Start the job:

```cmd
aws glue start-job-run --job-name dq-platform-customer-etl --profile admin --region us-west-2
```

Copy the returned JobRunId, then poll it:

```cmd
aws glue get-job-run --job-name dq-platform-customer-etl --run-id <JOB_RUN_ID> --query "JobRun.JobRunState" --output text --profile admin --region us-west-2
```

Expected: `SUCCEEDED`. If it fails, inspect the job run's `ErrorMessage`, `LogGroupName`, and CloudWatch logs before retrying.

Verify Parquet output:

```cmd
aws s3 ls s3://<CURATED_BUCKET>/customer/ --recursive --profile admin --region us-west-2
```

Expected: Parquet objects under a `processing_date=YYYY-MM-DD/` partition.

**Important:** Glue Crawler creation was previously rejected by this account with `AccessDeniedException: Account 553607360155 is denied access.` The ETL job reads direct S3 paths and does not need a crawler. The ETL job's successful execution must be verified independently.

## 4. Athena query example without a crawler

Open Athena in `us-west-2`, choose a query-results S3 location, and run the SQL in [customer_analytics.sql](../athena/customer_analytics.sql).

Before running, replace both occurrences of `<CURATED_BUCKET>` with the bucket name from `terraform output -raw curated_bucket_name`.

The SQL creates an external Parquet table using a direct S3 location and partition projection. It does not use a crawler. Then run the included state, city, volume, and null/blank checks.

Athena requires a configured query-results output location and IAM permissions for Athena, Glue Data Catalog metadata, and S3 data/query-results paths.

## 5. Optional crawler path when AWS account access is available

The optional Terraform resource is in `terraform/glue_crawler_optional.tf`. It is disabled by default.

After AWS Support confirms crawler creation is permitted, plan with:

```cmd
terraform plan -var="enable_glue_crawler=true"
```

Review the plan, then apply only if the crawler is the intended change:

```cmd
terraform apply -var="enable_glue_crawler=true"
```

Start and inspect it:

```cmd
aws glue start-crawler --name dq-platform-validated-crawler --profile admin --region us-west-2
aws glue get-crawler --name dq-platform-validated-crawler --query "Crawler.State" --output text --profile admin --region us-west-2
aws glue get-tables --database-name dq_platform --profile admin --region us-west-2
```

A crawler is optional for this direct-S3 ETL/Athena route. If used, it discovers source metadata in the Glue Data Catalog; do not point it at the curated Parquet path if you intend to use the explicit Athena table DDL above for that same table.

## Completion checklist

- [x] Terraform S3 zones and event-driven ingestion infrastructure deployed.
- [x] Valid JSON ingestion path exercised and validated output observed.
- [x] Schema comparison report generated and stored in S3.
- [x] Curated S3 bucket provisioned.
- [ ] Invalid fixture quarantine output independently verified.
- [ ] Glue job run reaches `SUCCEEDED`.
- [ ] Parquet output independently verified in curated S3.
- [ ] Athena DDL and sample queries executed successfully.
- [ ] Optional crawler tested only if AWS account access is granted.

Do not mark a cloud test complete based solely on Terraform resource creation. Record the job run ID, query execution ID, and observed output when each live test succeeds.
