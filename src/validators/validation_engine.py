
import json
from pathlib import Path
from collections import Counter


class ValidationEngine:

    def __init__(self, validator):
        self.validator = validator

    def validate_file(
        self,
        input_path: str,
        valid_path: str,
        invalid_path: str
    ):

        records = []

        with open(input_path, "r", encoding="utf-8") as file:

            for line_number, line in enumerate(file, start=1):

                if not line.strip():
                    continue

                try:
                    record = json.loads(line)

                    if not isinstance(record, dict):
                        raise ValueError("Expected JSON object")

                    records.append({
                        "record": record,
                        "line_number": line_number
                    })

                except (json.JSONDecodeError, ValueError) as exc:

                    records.append({
                        "record": None,
                        "line_number": line_number,
                        "parse_error": str(exc)
                    })

        # Count customer IDs across the complete batch.
        id_counts = Counter(
            item["record"].get("customer_id")
            for item in records
            if item["record"] is not None
            and isinstance(item["record"].get("customer_id"), str)
            and item["record"].get("customer_id")
        )

        valid_records = []
        invalid_records = []

        for item in records:

            record = item["record"]
            line_number = item["line_number"]

            if record is None:

                invalid_records.append({
                    "line_number": line_number,
                    "record": None,
                    "errors": [{
                        "error": "INVALID_JSON",
                        "details": item["parse_error"]
                    }]
                })
                continue

            errors = self.validator.validate(record)

            customer_id = record.get("customer_id")

            if customer_id and id_counts[customer_id] > 1:

                errors.append({
                    "field": "customer_id",
                    "error": "DUPLICATE_CUSTOMER_ID"
                })

            if errors:

                invalid_records.append({
                    "line_number": line_number,
                    "record": record,
                    "errors": errors
                })

            else:
                valid_records.append(record)

        self._write_jsonl(valid_path, valid_records)
        self._write_jsonl(invalid_path, invalid_records)

        total = len(records)
        valid_count = len(valid_records)
        invalid_count = len(invalid_records)

        return {
            "total_records": total,
            "valid_records": valid_count,
            "invalid_records": invalid_count,
            "quality_percentage": (
                round(valid_count / total * 100, 2)
                if total else 0
            ),
            "status": (
                "PASSED" if invalid_count == 0 else "FAILED"
            )
        }

    @staticmethod
    def _write_jsonl(path, records):

        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8") as file:

            for record in records:
                file.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )
