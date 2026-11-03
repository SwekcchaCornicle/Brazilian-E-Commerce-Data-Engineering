
import json
from pathlib import Path
from datetime import datetime, timezone


def generate_report(
    dataset_name: str,
    validation_summary: dict,
    output_path: str
):

    total = validation_summary["total_records"]
    invalid = validation_summary["invalid_records"]

    report = {
        "dataset_name": dataset_name,
        "execution_timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "total_records": total,
        "valid_records": validation_summary["valid_records"],
        "invalid_records": invalid,
        "quality_percentage": validation_summary[
            "quality_percentage"
        ],
        "status": validation_summary["status"]
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    return report
