
class BusinessValidator:

    BRAZILIAN_STATES = {
        "AC", "AL", "AP", "AM", "BA", "CE",
        "DF", "ES", "GO", "MA", "MT", "MS",
        "MG", "PA", "PB", "PR", "PE", "PI",
        "RJ", "RN", "RS", "RO", "RR", "SC",
        "SP", "SE", "TO"
    }

    def validate_customer(self, record: dict) -> list:

        errors = []

        city = record.get("customer_city")
        state = record.get("customer_state")
        zip_code = record.get("customer_zip_code_prefix")

        if isinstance(city, str) and not city.strip():
            errors.append({
                "field": "customer_city",
                "error": "EMPTY_CITY"
            })

        if state not in self.BRAZILIAN_STATES:
            errors.append({
                "field": "customer_state",
                "error": "INVALID_BRAZILIAN_STATE",
                "actual": state
            })

        if (
            not isinstance(zip_code, str)
            or len(zip_code) != 5
            or not zip_code.isdigit()
        ):
            errors.append({
                "field": "customer_zip_code_prefix",
                "error": "INVALID_ZIP_CODE"
            })

        return errors

    def validate_payment(self, record: dict) -> list:

        errors = []

        value = record.get("payment_value")

        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value <= 0
        ):
            errors.append({
                "field": "payment_value",
                "error": "PAYMENT_VALUE_MUST_BE_POSITIVE"
            })

        return errors

    def validate_review(self, record: dict) -> list:

        errors = []

        score = record.get("review_score")

        if (
            isinstance(score, (int, float))
            and not isinstance(score, bool)
            and not 1 <= score <= 5
        ):
            errors.append({
                "field": "review_score",
                "error": "REVIEW_SCORE_OUT_OF_RANGE"
            })

        return errors
