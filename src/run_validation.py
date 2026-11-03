
from src.schema_detector.schema_loader import load_schema

from src.validators.customer_validator import CustomerValidator
from src.validators.validation_engine import ValidationEngine

from src.utils.report_generator import generate_report


def main():

    schema = load_schema(
        "datasets/schemas/customers/v1.json"
    )

    validator = CustomerValidator(schema)

    engine = ValidationEngine(validator)

    summary = engine.validate_file(
        input_path="datasets/test_data/customers_test.jsonl",
        valid_path="reports/valid/customers.jsonl",
        invalid_path="reports/invalid/customers.jsonl"
    )

    report = generate_report(
        dataset_name="customers",
        validation_summary=summary,
        output_path="reports/customers_quality_report.json"
    )

    print("DATA QUALITY REPORT")
    print("-------------------")

    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
