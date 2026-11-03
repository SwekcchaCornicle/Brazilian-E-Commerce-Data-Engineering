
from src.validators.customer_validator import CustomerValidator
from src.validators.validation_engine import ValidationEngine


def test_valid_customer(schema):
    validator = CustomerValidator(schema)

    record = {
        "customer_id": "C101",
        "customer_unique_id": "U101",
        "customer_zip_code_prefix": "01310",
        "customer_city": "sao paulo",
        "customer_state": "SP"
    }

    assert validator.validate(record) == []


def test_null_customer_id(schema):
    validator = CustomerValidator(schema)

    record = {
        "customer_id": None,
        "customer_unique_id": "U101",
        "customer_zip_code_prefix": "01310",
        "customer_city": "sao paulo",
        "customer_state": "SP"
    }

    errors = validator.validate(record)

    assert any(
        error["field"] == "customer_id"
        for error in errors
    )


def test_invalid_state(schema):
    validator = CustomerValidator(schema)

    record = {
        "customer_id": "C101",
        "customer_unique_id": "U101",
        "customer_zip_code_prefix": "01310",
        "customer_city": "sao paulo",
        "customer_state": "XX"
    }

    errors = validator.validate(record)

    assert any(
        error["error"] == "INVALID_BRAZILIAN_STATE"
        for error in errors
    )


def test_invalid_zip_code(schema):
    validator = CustomerValidator(schema)

    record = {
        "customer_id": "C101",
        "customer_unique_id": "U101",
        "customer_zip_code_prefix": "ABC",
        "customer_city": "sao paulo",
        "customer_state": "SP"
    }

    errors = validator.validate(record)

    assert any(
        error["error"] == "INVALID_ZIP_CODE"
        for error in errors
    )
