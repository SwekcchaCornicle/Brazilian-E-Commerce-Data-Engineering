
def compare_schemas(old_schema: dict, new_schema: dict) -> dict:

    old_fields = old_schema["fields"]
    new_fields = new_schema["fields"]

    added_fields = []
    removed_fields = []
    modified_fields = []
    breaking_changes = []
    compatible_changes = []

    # 1. Detect added fields
    for field in new_fields:

        if field not in old_fields:

            change = {
                "field": field,
                "change": "FIELD_ADDED",
                "required": new_fields[field].get(
                    "required", False
                )
            }

            added_fields.append(change)

            if change["required"]:
                breaking_changes.append(change)
            else:
                compatible_changes.append(change)

    # 2. Detect removed fields
    for field in old_fields:

        if field not in new_fields:

            change = {
                "field": field,
                "change": "FIELD_REMOVED"
            }

            removed_fields.append(change)
            breaking_changes.append(change)

    # 3. Detect modified fields
    for field in old_fields:

        if field not in new_fields:
            continue

        old_type = old_fields[field]["type"]
        new_type = new_fields[field]["type"]

        if old_type != new_type:

            change = {
                "field": field,
                "change": "DATA_TYPE_CHANGED",
                "old_type": old_type,
                "new_type": new_type
            }

            modified_fields.append(change)
            breaking_changes.append(change)

        old_required = old_fields[field].get(
            "required", False
        )

        new_required = new_fields[field].get(
            "required", False
        )

        if old_required != new_required:

            change = {
                "field": field,
                "change": "REQUIREDNESS_CHANGED",
                "old_required": old_required,
                "new_required": new_required
            }

            modified_fields.append(change)

            if new_required:
                breaking_changes.append(change)
            else:
                compatible_changes.append(change)

        old_nullable = old_fields[field].get(
            "nullable", False
        )

        new_nullable = new_fields[field].get(
            "nullable", False
        )

        if old_nullable != new_nullable:

            change = {
                "field": field,
                "change": "NULLABILITY_CHANGED",
                "old_nullable": old_nullable,
                "new_nullable": new_nullable
            }

            modified_fields.append(change)

            if new_nullable:
                compatible_changes.append(change)
            else:
                breaking_changes.append(change)

    # 4. Determine final status
    if breaking_changes:
        status = "BREAKING_CHANGE"

    elif added_fields or removed_fields or modified_fields:
        status = "BACKWARD_COMPATIBLE"

    else:
        status = "NO_CHANGE"

    return {
        "schema_changed": status != "NO_CHANGE",
        "status": status,
        "added_fields": added_fields,
        "removed_fields": removed_fields,
        "modified_fields": modified_fields,
        "breaking_changes": breaking_changes,
        "compatible_changes": compatible_changes
    }
