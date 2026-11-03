import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F


CUSTOMER_FIELDS = (
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state",
)

# Match the Lambda ingestion contract. Optional Olist fields are retained.
REQUIRED_FIELDS = (
    "customer_id",
    "customer_city",
    "customer_state",
)


def main():
    args = getResolvedOptions(
        sys.argv,
        ["JOB_NAME", "INPUT_PATH", "OUTPUT_PATH"],
    )

    sc = SparkContext.getOrCreate()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session

    job = Job(glue_context)
    job.init(args["JOB_NAME"], args)

    input_path = args["INPUT_PATH"]
    output_path = args["OUTPUT_PATH"]

    print(f"Reading validated JSON Lines from: {input_path}")

    # Lambda writes one JSON object per line (NDJSON), which Spark reads
    # using the default JSON Lines mode.
    df = spark.read.json(input_path)

    # Keep a stable five-column customer shape and preserve zip prefixes
    # as strings so leading zeroes are not lost.
    for field in CUSTOMER_FIELDS:
        if field not in df.columns:
            df = df.withColumn(field, F.lit(None).cast("string"))
        else:
            df = df.withColumn(
                field,
                F.trim(F.col(field).cast("string")),
            )

    df = df.withColumn(
        "customer_state",
        F.upper(F.col("customer_state")),
    )

    valid_condition = F.lit(True)
    for field in REQUIRED_FIELDS:
        valid_condition = (
            valid_condition
            & F.col(field).isNotNull()
            & (F.trim(F.col(field)) != "")
        )

    total_count = df.count()
    valid_df = df.filter(valid_condition)
    rejected_count = total_count - valid_df.count()

    print(
        f"ETL quality summary: total_records={total_count}, "
        f"valid_records={total_count - rejected_count}, "
        f"rejected_records={rejected_count}"
    )

    output_df = (
        valid_df
        .withColumn("processed_at", F.current_timestamp())
        .withColumn("processing_date", F.current_date())
    )

    (
        output_df.write
        .mode("append")
        .partitionBy("processing_date")
        .parquet(output_path)
    )

    print(f"Curated Parquet written to: {output_path}")
    job.commit()


if __name__ == "__main__":
    main()
