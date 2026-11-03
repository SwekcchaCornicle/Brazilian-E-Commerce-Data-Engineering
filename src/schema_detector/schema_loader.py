
import json
from pathlib import Path


def load_schema(schema_path: str) -> dict:
    """Load a registered schema from a JSON file."""

    path = Path(schema_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Schema not found: {schema_path}"
        )

    with path.open("r", encoding="utf-8") as file:
        schema = json.load(file)

    if "fields" not in schema:
        raise ValueError("Schema must contain fields")

    return schema
