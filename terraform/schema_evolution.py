import json
from pathlib import Path
from typing import Any


def load_schema(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def compare_schemas(
    old_schema: dict[str, Any],
    new_schema: dict[str, Any],
) -> dict[str, Any]:
    old_properties = old_schema.get("properties", {})
    new_properties = new_schema.get("properties", {})
    old_required = set(old_schema.get("required", []))
    new_required = set(new_schema.get("required", []))
    old_fields = set(old_properties)
    new_fields = set(new_properties)

    added_fields = sorted(new_fields - old_fields)
    removed_fields = sorted(old_fields - new_fields)
    type_changes = [
        {
            "field": field,
            "old_type": old_properties[field].get("type"),
            "new_type": new_properties[field].get("type"),
        }
        for field in sorted(old_fields & new_fields)
        if old_properties[field].get("type")
        != new_properties[field].get("type")
    ]
    newly_required = sorted(new_required - old_required)
    no_longer_required = sorted(old_required - new_required)

    breaking_changes = [
        *(f"Removed field: {field}" for field in removed_fields),
        *(
            f"Changed type for field: {change['field']}"
            for change in type_changes
        ),
        *(f"Newly required field: {field}" for field in newly_required),
    ]

    return {
        "added_fields": added_fields,
        "removed_fields": removed_fields,
        "type_changes": type_changes,
        "newly_required": newly_required,
        "no_longer_required": no_longer_required,
        "breaking_changes": breaking_changes,
        "compatible": not breaking_changes,
    }


def main() -> None:
    schema_dir = Path(__file__).resolve().parent / "schemas" / "customer"
    old_schema = load_schema(schema_dir / "v2" / "schema.json")
    new_schema = load_schema(schema_dir / "v3" / "schema.json")
    print(json.dumps(compare_schemas(old_schema, new_schema), indent=4))


if __name__ == "__main__":
    main()
