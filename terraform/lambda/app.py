
import json
import os
import urllib.parse
import boto3
from datetime import datetime, timezone

s3 = boto3.client("s3")

VALIDATED_BUCKET = os.environ["VALIDATED_BUCKET"]
QUARANTINE_BUCKET = os.environ["QUARANTINE_BUCKET"]

REQUIRED_FIELDS = [
    "customer_id",
    "customer_city",
    "customer_state",
]


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


def process_s3_event(event):
    detail = event.get("detail", {})

    bucket = detail.get("bucket", {}).get("name")
    key = detail.get("object", {}).get("key")

    if not bucket or not key:
        raise ValueError("EventBridge event is missing S3 bucket or object key")

    key = urllib.parse.unquote_plus(key)

    response = s3.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    records = data if isinstance(data, list) else [data]

    valid_records = []
    invalid_records = []

    for index, record in enumerate(records):
        errors = validate_record(record)

        if errors:
            invalid_records.append({
                "record_index": index,
                "record": record,
                "errors": errors
            })
        else:
            valid_records.append(record)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_key = f"processed/{timestamp}/{key.rsplit('/', 1)[-1]}.json"

    if valid_records:
        s3.put_object(
            Bucket=VALIDATED_BUCKET,
            Key=output_key,
            Body=json.dumps(valid_records).encode("utf-8"),
            ContentType="application/json"
        )

    if invalid_records:
        quarantine_key = f"quarantine/{timestamp}/{key.rsplit('/', 1)[-1]}.json"

        s3.put_object(
            Bucket=QUARANTINE_BUCKET,
            Key=quarantine_key,
            Body=json.dumps(invalid_records).encode("utf-8"),
            ContentType="application/json"
        )

    return {
        "source": f"s3://{bucket}/{key}",
        "total_records": len(records),
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records)
    }


def lambda_handler(event, context):
    results = []
    batch_item_failures = []

    for message in event.get("Records", []):
        try:
            eventbridge_event = json.loads(message["body"])
            result = process_s3_event(eventbridge_event)
            results.append(result)
            print(json.dumps(result))

        except Exception as exc:
            print(f"Failed message {message['messageId']}: {exc}")
            batch_item_failures.append({
                "itemIdentifier": message["messageId"]
            })

    return {
        "batchItemFailures": batch_item_failures,
        "results": results
    }