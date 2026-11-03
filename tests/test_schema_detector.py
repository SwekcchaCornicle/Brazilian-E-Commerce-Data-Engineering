
from src.schema_detector.schema_comparator import compare_schemas


def make_schema(fields):
    return {"fields": fields}


def test_optional_field_addition():
    old = make_schema({
        "customer_id": {
            "type": "string",
            "required": True,
            "nullable": False
        }
    })

    new = make_schema({
        "customer_id": {
            "type": "string",
            "required": True,
            "nullable": False
        },
        "customer_segment": {
            "type": "string",
            "required": False,
            "nullable": True
        }
    })

    result = compare_schemas(old, new)

    assert result["status"] == "BACKWARD_COMPATIBLE"
    assert len(result["added_fields"]) == 1
    assert len(result["breaking_changes"]) == 0


def test_required_field_addition():
    old = make_schema({
        "customer_id": {
            "type": "string",
            "required": True
        }
    })

    new = make_schema({
        "customer_id": {
            "type": "string",
            "required": True
        },
        "email": {
            "type": "string",
            "required": True
        }
    })

    result = compare_schemas(old, new)

    assert result["status"] == "BREAKING_CHANGE"


def test_field_removal():
    old = make_schema({
        "customer_id": {"type": "string"},
        "customer_city": {"type": "string"}
    })

    new = make_schema({
        "customer_id": {"type": "string"}
    })

    result = compare_schemas(old, new)

    assert result["status"] == "BREAKING_CHANGE"
    assert result["removed_fields"][0]["field"] == "customer_city"


def test_data_type_change():
    old = make_schema({
        "customer_id": {"type": "integer"}
    })

    new = make_schema({
        "customer_id": {"type": "string"}
    })

    result = compare_schemas(old, new)

    assert result["status"] == "BREAKING_CHANGE"


def test_no_schema_change():
    schema = make_schema({
        "customer_id": {
            "type": "string",
            "required": True,
            "nullable": False
        }
    })

    result = compare_schemas(schema, schema)

    assert result["status"] == "NO_CHANGE"
    assert result["schema_changed"] is False
