import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

SCHEMA_V2 = BASE_DIR / "schemas" / "customer" / "v2" / "schema.json"
SCHEMA_V3 = BASE_DIR / "schemas" / "customer" / "v3" / "schema.json"


def normalize_types(value):
    if value is None:
        return set()
    if isinstance(value, list):
        return set(value)
    return {value}


def compare_schema(old_schema, new_schema, path="$"):
    changes = []

    old_types = normalize_types(old_schema.get("type"))
    new_types = normalize_types(new_schema.get("type"))

    if old_types and new_types and old_types != new_types:
        changes.append({
            "type": "type_changed",
            "path": path,
            "old": sorted(old_types),
            "new": sorted(new_types)
        })

    old_required = set(old_schema.get("required", []))
    new_required = set(new_schema.get("required", []))
    old_properties = old_schema.get("properties", {})
    new_properties = new_schema.get("properties", {})

    for field in sorted(new_required - old_required):
        changes.append({
            "type": "field_became_required",
            "path": f"{path}.{field}"
        })

    for field in sorted((old_required - new_required) & new_properties.keys()):
        changes.append({
            "type": "field_became_optional",
            "path": f"{path}.{field}"
        })

    for field in sorted(old_properties.keys() - new_properties.keys()):
        changes.append({
            "type": "field_removed",
            "path": f"{path}.{field}"
        })

    for field in sorted(new_properties.keys() - old_properties.keys()):
        changes.append({
            "type": "field_added",
            "path": f"{path}.{field}"
        })

    for field in sorted(old_properties.keys() & new_properties.keys()):
        changes.extend(
            compare_schema(
                old_properties[field],
                new_properties[field],
                f"{path}.{field}"
            )
        )

    old_items = old_schema.get("items")
    new_items = new_schema.get("items")

    if old_items and new_items:
        changes.extend(
            compare_schema(old_items, new_items, f"{path}[]")
        )
    elif old_items and not new_items:
        changes.append({
            "type": "array_items_removed",
            "path": f"{path}[]"
        })
    elif new_items and not old_items:
        changes.append({
            "type": "array_items_added",
            "path": f"{path}[]"
        })

    old_enum = set(old_schema.get("enum", []))
    new_enum = set(new_schema.get("enum", []))

    if old_enum and new_enum and old_enum != new_enum:
        changes.append({
            "type": "enum_changed",
            "path": path,
            "removed_values": sorted(old_enum - new_enum),
            "added_values": sorted(new_enum - old_enum)
        })

    constraint_keys = [
        "minimum",
        "maximum",
        "minLength",
        "maxLength",
        "pattern",
        "minItems",
        "maxItems"
    ]

    for key in constraint_keys:
        old_value = old_schema.get(key)
        new_value = new_schema.get(key)

        if old_value != new_value and (key in old_schema or key in new_schema):
            changes.append({
                "type": "constraint_changed",
                "path": path,
                "constraint": key,
                "old": old_value,
                "new": new_value
            })

    return changes


def classify_changes(changes):
    breaking_types = {
        "field_removed",
        "field_became_required",
        "type_changed",
        "array_items_removed"
    }

    review_types = {
        "enum_changed",
        "constraint_changed",
        "field_added",
        "field_became_optional",
        "array_items_added"
    }

    breaking = []
    review_required = []
    non_breaking = []

    for change in changes:
        change_type = change["type"]

        if change_type in breaking_types:
            breaking.append(change)
        elif change_type in review_types:
            review_required.append(change)
        else:
            non_breaking.append(change)

    return {
        "breaking": breaking,
        "review_required": review_required,
        "non_breaking": non_breaking,
        "compatible": len(breaking) == 0
    }


def main():
    with open(SCHEMA_V2, encoding="utf-8") as file:
        old_schema = json.load(file)

    with open(SCHEMA_V3, encoding="utf-8") as file:
        new_schema = json.load(file)

    changes = compare_schema(old_schema, new_schema)
    result = classify_changes(changes)

    print("\n========== ADVANCED SCHEMA EVOLUTION ==========")
    print("Old schema: v2")
    print("New schema: v3")

    print("\nDetected changes:")
    print(json.dumps(changes, indent=4))

    print("\nCompatibility classification:")
    print(json.dumps(result, indent=4))

    print("\nFinal compatibility:", result["compatible"])


if __name__ == "__main__":
    main()
