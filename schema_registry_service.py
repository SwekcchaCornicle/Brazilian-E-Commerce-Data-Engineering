import json
import re
from datetime import datetime, timezone
from typing import Any

import boto3

from terraform.schema_evolution import compare_schemas


AWS_PROFILE = "admin"
AWS_REGION = "us-west-2"
SCHEMA_BUCKET = "dq-platform-schemas-791c8f1e"
REPORT_BUCKET = "dq-platform-reports-791c8f1e"
DATASET = "customer"

session = boto3.Session(
    profile_name=AWS_PROFILE,
    region_name=AWS_REGION,
)
s3 = session.client("s3")


def get_schema_versions() -> list[tuple[int, str]]:
    paginator = s3.get_paginator("list_objects_v2")
    versions = []
    pattern = re.compile(rf"{re.escape(DATASET)}/v(\d+)/schema\.json")

    for page in paginator.paginate(
        Bucket=SCHEMA_BUCKET,
        Prefix=f"{DATASET}/",
    ):
        for item in page.get("Contents", []):
            key = item["Key"]
            match = pattern.fullmatch(key)
            if match:
                versions.append((int(match.group(1)), key))

    return sorted(versions)


def load_s3_schema(key: str) -> dict[str, Any]:
    response = s3.get_object(Bucket=SCHEMA_BUCKET, Key=key)
    schema = json.loads(response["Body"].read().decode("utf-8"))
    if not isinstance(schema, dict):
        raise ValueError(f"Schema at s3://{SCHEMA_BUCKET}/{key} must be a JSON object")
    return schema


def run_comparison() -> dict[str, Any]:
    versions = get_schema_versions()
    if len(versions) < 2:
        raise RuntimeError(
            f"At least two schema versions are required in s3://{SCHEMA_BUCKET}/{DATASET}/"
        )

    (old_version, old_key), (new_version, new_key) = versions[-2:]
    comparison = compare_schemas(
        load_s3_schema(old_key),
        load_s3_schema(new_key),
    )

    timestamp = datetime.now(timezone.utc)
    timestamp_text = timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    report_key = (
        f"schema-evolution/{DATASET}/v{new_version}/"
        f"v{old_version}-to-v{new_version}-{timestamp_text}.json"
    )
    report_uri = f"s3://{REPORT_BUCKET}/{report_key}"
    report = {
        "dataset": DATASET,
        "old_version": old_version,
        "new_version": new_version,
        "generated_at": timestamp.isoformat(),
        "report_s3_uri": report_uri,
        **comparison,
    }

    s3.put_object(
        Bucket=REPORT_BUCKET,
        Key=report_key,
        Body=json.dumps(report, indent=4).encode("utf-8"),
        ContentType="application/json",
    )
    return report


def main() -> None:
    print(json.dumps(run_comparison(), indent=4))


if __name__ == "__main__":
    main()
