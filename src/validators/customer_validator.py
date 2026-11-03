
from .field_validator import FieldValidator
from .business_validator import BusinessValidator


class CustomerValidator:

    def __init__(self, schema: dict):

        self.field_validator = FieldValidator(schema)
        self.business_validator = BusinessValidator()

    def validate(self, record: dict) -> list:

        errors = []

        errors.extend(
            self.field_validator.validate(record)
        )

        errors.extend(
            self.business_validator.validate_customer(record)
        )

        return errors
