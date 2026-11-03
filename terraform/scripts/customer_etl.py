import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F


REQUIRED_FIELDS = ("customer_id", "customer_city", "customer_state")


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
    print(f"Reading customer data from: {input_path}")

    df = spark.read.option("multiLine", "true").json(input_path)

    for field in REQUIRED_FIELDS:
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

    valid_condition = (
        F.col("customer_id").isNotNull()
        & (F.col("customer_id") != "")
        & F.col("customer_city").isNotNull()
        & (F.col("customer_city") != "")
        & F.col("customer_state").isNotNull()
        & (F.col("customer_state") != "")
    )
    valid_df = df.filter(valid_condition)
    rejected_count = df.filter(~valid_condition).count()
    print(f"Rejected records with missing or blank required fields: {rejected_count}")

    output_df = (
        valid_df
        .withColumn("processed_at", F.current_timestamp())
        .withColumn("processing_date", F.current_date())
    )

    print(f"Writing curated customer data to: {output_path}")
    (
        output_df.write
        .mode("append")
        .partitionBy("processing_date")
        .parquet(output_path)
    )

    job.commit()


if __name__ == "__main__":
    main()
