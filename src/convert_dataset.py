import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "datasets" / "source"
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "raw"

DATASETS = {
    "olist_customers_dataset.csv": "customers",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_products_dataset.csv": "products",
    "olist_order_payments_dataset.csv": "payments",
    "olist_order_reviews_dataset.csv": "reviews",
}


def convert_csv_to_jsonl(filename: str, dataset_name: str) -> int:
    input_file = SOURCE_DIR / filename
    output_dir = OUTPUT_DIR / dataset_name / "v1"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "data.jsonl"

    count = 0
    with input_file.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        with output_file.open("w", encoding="utf-8", newline="\n") as json_file:
            for row in reader:
                record = {
                    key: value if value != "" else None
                    for key, value in row.items()
                }
                json_file.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )
                count += 1

    return count


def main() -> None:
    for filename, dataset_name in DATASETS.items():
        count = convert_csv_to_jsonl(filename, dataset_name)
        output_file = OUTPUT_DIR / dataset_name / "v1" / "data.jsonl"
        print(f"Converted {dataset_name}: {count} records")
        print(f"Output: {output_file.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
