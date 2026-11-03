import json
import os
import urllib.parse
from datetime import datetime, timezone

import boto3

s3 = boto3.client("s3")

VALIDATED_BUCKET = os.environ["VALIDATED_BUCKET"]
QUARANTINE_BUCKET = os.environ["QUARANTINE_BUCKET"]
REPORTS_BUCKET = os.environ["REPORTS_BUCKET"]

# The ingestion contract requires these three fields.
# Other Olist customer attributes are retained when supplied.
REQUIRED_FIELDS = (
    "customer_id",
    "customer_city",
    "customer_state",
)


def validate_record(record):
    errors = []

    if not isinstance(record, dict):
        return ["Record must be a JSON object"]

    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append(f"Missing required field: {field}")
        elif record[field] is None or str(record[field]).strip() == "":
            errors.append(f"Empty required field: {field}")

    return errors


def _write_json_lines(bucket, key, records):
    body = "\n".join(
        json.dumps(record, ensure_ascii=False)
        for record in records
    )
    if body:
        body += "\n"

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/x-ndjson",
    )


def process_s3_event(event):
    detail = event.get("detail", {})
    source_bucket = detail.get("bucket", {}).get("name")
    source_key = detail.get("object", {}).get("key")

    if not source_bucket or not source_key:
        raise ValueError("EventBridge event is missing S3 bucket or object key")

    source_key = urllib.parse.unquote_plus(source_key)
    response = s3.get_object(Bucket=source_bucket, Key=source_key)
    content = response["Body"].read().decode("utf-8")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    records = data if isinstance(data, list) else [data]
    valid_records = []
    invalid_records = []
    validation_errors = []

    for index, record in enumerate(records):
        errors = validate_record(record)
        if errors:
            invalid_records.append({
                "record_index": index,
                "record": record,
                "errors": errors,
            })
            validation_errors.append({
                "record_index": index,
                "errors": errors,
            })
        else:
            valid_records.append(record)

    # Microseconds reduce collisions between same-name objects processed
    # during the same second. SQS retry idempotency is still a future hardening item.
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    filename = source_key.rsplit("/", 1)[-1] or "input.json"

    validated_key = None
    quarantine_key = None

    if valid_records:
        validated_key = f"processed/{timestamp}/{filename}"
        _write_json_lines(VALIDATED_BUCKET, validated_key, valid_records)

    if invalid_records:
        quarantine_key = f"quarantine/{timestamp}/{filename}"
        _write_json_lines(QUARANTINE_BUCKET, quarantine_key, invalid_records)

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": f"s3://{source_bucket}/{source_key}",
        "total_records": len(records),
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "validated_output": (
            f"s3://{VALIDATED_BUCKET}/{validated_key}"
            if validated_key else None
        ),
        "quarantine_output": (
            f"s3://{QUARANTINE_BUCKET}/{quarantine_key}"
            if quarantine_key else None
        ),
        "validation_errors": validation_errors,
    }

    report_key = f"ingestion-reports/{timestamp}/{filename}.report.json"
    s3.put_object(
        Bucket=REPORTS_BUCKET,
        Key=report_key,
        Body=json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
    )

    result = {
        **report,
        "report_output": f"s3://{REPORTS_BUCKET}/{report_key}",
    }
    return result


def lambda_handler(event, context):
    results = []
    batch_item_failures = []

    for message in event.get("Records", []):
        try:
            eventbridge_event = json.loads(message["body"])
            result = process_s3_event(eventbridge_event)
            results.append(result)
            # CloudWatch receives the same compact per-object summary.
            print(json.dumps(result, ensure_ascii=False))
        except Exception as exc:
            print(f"Failed message {message['messageId']}: {exc}")
            batch_item_failures.append({
                "itemIdentifier": message["messageId"]
            })

    return {
        "batchItemFailures": batch_item_failures,
        "results": results,
    }


if __name__ == "__main__":
    # AWS Lambda invokes lambda_handler; this guard supports syntax tooling.
    pass
