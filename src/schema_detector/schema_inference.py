
import json
from decimal import Decimal
from pathlib import Path


def get_data_type(value):
    """Identify the JSON-compatible Python data type."""

    if value is None:
        return "null"

    if isinstance(value, bool):
        return "boolean"

    if isinstance(value, int):
        return "integer"

    if isinstance(value, (float, Decimal)):
        return "number"

    if isinstance(value, str):
        return "string"

    if isinstance(value, list):
        return "array"

    if isinstance(value, dict):
        return "object"

    return "unknown"


def infer_schema(jsonl_path: str) -> dict:
    """Infer field types and nullability from JSONL records."""

    path = Path(jsonl_path)

    if not path.exists():
        raise FileNotFoundError(jsonl_path)

    fields = {}
    record_count = 0

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):

            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number}"
                ) from exc

            if not isinstance(record, dict):
                raise ValueError(
                    f"Expected JSON object at line {line_number}"
                )

            record_count += 1

            for field, value in record.items():

                detected_type = get_data_type(value)

                if field not in fields:
                    fields[field] = {
                        "types": set(),
                        "required": True
                    }

                fields[field]["types"].add(detected_type)

            for field in fields:
                if field not in record:
                    fields[field]["required"] = False

    result = {}

    for field, metadata in fields.items():

        types = metadata["types"]
        nullable = "null" in types

        non_null_types = types - {"null"}

        result[field] = {
            "type": (
                list(sorted(non_null_types))
                if len(non_null_types) > 1
                else next(iter(non_null_types), "null")
            ),
            "required": metadata["required"],
            "nullable": nullable
        }

    return {
        "record_count": record_count,
        "fields": result
    }
