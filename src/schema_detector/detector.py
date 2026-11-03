
import json
from datetime import datetime, timezone
from pathlib import Path

from src.schema_detector.schema_loader import load_schema
from src.schema_detector.schema_comparator import compare_schemas


def detect_schema_changes(
    old_schema_path: str,
    new_schema_path: str,
    report_path: str
):

    old_schema = load_schema(old_schema_path)
    new_schema = load_schema(new_schema_path)

    comparison = compare_schemas(
        old_schema,
        new_schema
    )

    report = {
        "dataset": new_schema.get("dataset_name"),
        "old_version": old_schema.get("schema_version"),
        "new_version": new_schema.get("schema_version"),
        "detected_at": datetime.now(
            timezone.utc
        ).isoformat(),
        **comparison
    }

    output = Path(report_path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    return report


if __name__ == "__main__":

    result = detect_schema_changes(
        "datasets/schemas/customers/v1.json",
        "datasets/schemas/customers/v2.json",
        "reports/customers_schema_report.json"
    )

    print(json.dumps(result, indent=4))
