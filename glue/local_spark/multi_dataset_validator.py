
from functools import reduce

from pyspark.sql import functions as F


def build_validation_errors(df, rules):

    errors = []

    # 1. Required field validation
    for field in rules.get("required_fields", []):

        if field not in df.columns:
            errors.append(
                F.lit(f"MISSING_COLUMN:{field}")
            )
        else:
            value = F.col(field)

            errors.append(
                F.when(
                    value.isNull() |
                    (F.trim(value.cast("string")) == ""),
                    F.lit(f"REQUIRED_VALUE_MISSING:{field}")
                )
            )

    # 2. Allowed values
    for field, allowed in rules.get(
        "valid_values", {}
    ).items():

        if field in df.columns:

            errors.append(
                F.when(
                    ~F.col(field).isin(allowed) &
                    F.col(field).isNotNull(),
                    F.lit(f"INVALID_VALUE:{field}")
                )
            )

    # 3. Positive numeric values
    for field in rules.get("positive_fields", []):

        if field in df.columns:

            errors.append(
                F.when(
                    F.col(field).isNotNull() &
                    (
                        F.col(field).cast("double").isNull() |
                        (F.col(field).cast("double") <= 0)
                    ),
                    F.lit(f"INVALID_POSITIVE_VALUE:{field}")
                )
            )

    # 4. Numeric ranges
    for field, limits in rules.get(
        "valid_ranges", {}
    ).items():

        if field in df.columns:

            value = F.col(field).cast("double")

            errors.append(
                F.when(
                    F.col(field).isNotNull() &
                    (
                        value.isNull() |
                        (value < limits["min"]) |
                        (value > limits["max"])
                    ),
                    F.lit(f"OUT_OF_RANGE:{field}")
                )
            )

    # Combine all validation errors
    if not errors:
        return F.array().cast("array<string>")

    return F.filter(
        F.array(*errors),
        lambda x: x.isNotNull()
    )


def validate_dataset(df, rules):

    # Detect missing columns before validation
    missing_columns = [
        field
        for field in rules.get("required_fields", [])
        if field not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Schema validation failed. Missing columns: "
            f"{missing_columns}"
        )

    # Generate field-level errors
    validated = df.withColumn(
        "validation_errors",
        build_validation_errors(df, rules)
    )

    # 5. Duplicate detection
    unique_fields = rules.get(
        "unique_fields",
        rules.get("primary_key", [])
    )

    if unique_fields:

        duplicates = (
            df.groupBy(*unique_fields)
            .count()
            .filter(F.col("count") > 1)
            .select(*unique_fields)
            .withColumn("is_duplicate", F.lit(True))
        )

        validated = validated.join(
            duplicates,
            on=unique_fields,
            how="left"
        )

        validated = (
            validated
            .withColumn(
                "validation_errors",
                F.when(
                    F.col("is_duplicate") == True,
                    F.concat(
                        F.col("validation_errors"),
                        F.array(
                            F.lit("DUPLICATE_PRIMARY_KEY")
                        )
                    )
                ).otherwise(F.col("validation_errors"))
            )
            .drop("is_duplicate")
        )

    valid_df = validated.filter(
        F.size("validation_errors") == 0
    )

    invalid_df = validated.filter(
        F.size("validation_errors") > 0
    )

    return valid_df, invalid_df
