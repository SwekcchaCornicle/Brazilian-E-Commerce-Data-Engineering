
from pyspark.sql import functions as F


def find_orphan_records(
    child_df,
    parent_df,
    child_key,
    parent_key,
    relationship_name
):
    """
    Find records in child_df that have no matching
    key in parent_df.
    """

    child = child_df.alias("child")

    parent_keys = (
        parent_df
        .select(F.col(parent_key).alias("_parent_key"))
        .filter(F.col("_parent_key").isNotNull())
        .dropDuplicates()
    )

    joined = child.join(
        parent_keys.alias("parent"),
        F.col(f"child.{child_key}") ==
        F.col("parent._parent_key"),
        "left"
    )

    return (
        joined
        .filter(F.col("parent._parent_key").isNull())
        .select("child.*")
        .withColumn(
            "referential_error",
            F.lit(f"ORPHAN_REFERENCE:{relationship_name}")
        )
    )
