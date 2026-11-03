
class FieldValidator:

    def __init__(self, schema: dict):
        self.schema = schema["fields"]

    def validate(self, record: dict) -> list:

        errors = []

        for field, rules in self.schema.items():

            value = record.get(field)

            # Mandatory field check
            if rules.get("required", False):
                if field not in record:
                    errors.append({
                        "field": field,
                        "error": "MISSING_REQUIRED_FIELD"
                    })
                    continue

            # Null check
            if value is None:

                if not rules.get("nullable", True):
                    errors.append({
                        "field": field,
                        "error": "NULL_VALUE_NOT_ALLOWED"
                    })

                continue

            # Type validation
            expected_type = rules.get("type")

            actual_type = self.get_type(value)

            if expected_type and actual_type != expected_type:

                errors.append({
                    "field": field,
                    "error": "INVALID_DATA_TYPE",
                    "expected": expected_type,
                    "actual": actual_type
                })

        return errors

    @staticmethod
    def get_type(value):

        if isinstance(value, bool):
            return "boolean"

        if isinstance(value, int):
            return "integer"

        if isinstance(value, float):
            return "number"

        if isinstance(value, str):
            return "string"

        if isinstance(value, list):
            return "array"

        if isinstance(value, dict):
            return "object"

        if value is None:
            return "null"

        return "unknown"
