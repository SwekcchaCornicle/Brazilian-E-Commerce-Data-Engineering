import pytest
from src.schema_detector.schema_loader import load_schema


@pytest.fixture
def schema():
    return load_schema(
        "datasets/schemas/customers/v1.json"
    )