
import json
from pathlib import Path

from glue.local_spark.spark_session import create_spark_session
from glue.local_spark.multi_dataset_validator import validate_dataset
from glue.local_spark.referential_validator import find_orphan_records

import time

start_time = time.perf_counter()

# Execute dataset validation here



def load_rules(path):

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def main():

    spark = create_spark_session()

    rules = load_rules(
        "datasets/schemas/validation_rules.json"
    )

    dataset_names = [
        "customers",
        "orders",
        "order_items",
        "products",
        "payments",
        "reviews"
    ]

    dataframes = {}
    summaries = {}

    for name in dataset_names:

        print(f"Processing dataset: {name}")

        input_path = f"datasets/raw/{name}/v1/data.jsonl"

        df = spark.read.json(input_path)

        valid_df, invalid_df = validate_dataset(
            df,
            rules[name]
        )

        output_base = f"reports/pyspark/{name}"

        valid_df.write.mode("overwrite").parquet(
            f"{output_base}/valid"
        )

        invalid_df.write.mode("overwrite").parquet(
            f"{output_base}/invalid"
        )

        total = df.count()
        valid_count = valid_df.count()
        invalid_count = invalid_df.count()

        summaries[name] = {
            "total": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "quality_percentage": (
                round(valid_count / total * 100, 2)
                if total else 0
            )
        }

        dataframes[name] = valid_df

    # Referential integrity checks
    relationships = [
        ("orders", "customers", "customer_id", "customer_id"),
        ("order_items", "orders", "order_id", "order_id"),
        ("order_items", "products", "product_id", "product_id"),
        ("payments", "orders", "order_id", "order_id"),
        ("reviews", "orders", "order_id", "order_id")
    ]

    for child, parent, child_key, parent_key in relationships:

        orphan_df = find_orphan_records(
            dataframes[child],
            dataframes[parent],
            child_key,
            parent_key,
            f"{child}_{parent}"
        )

        orphan_count = orphan_df.count()

        orphan_df.write.mode("overwrite").parquet(
            f"reports/pyspark/referential/{child}_{parent}"
        )

        print(
            f"{child} -> {parent}: "
            f"{orphan_count} orphan records"
        )

    print("\nDATASET QUALITY SUMMARY")

    for name, summary in summaries.items():
        print(name, summary)

    spark.stop()


if __name__ == "__main__":
    main()
    end_time = time.perf_counter()

    execution_time = round(
        end_time - start_time, 2
    )

    print(f"Execution time: {execution_time} seconds")
