import pytest

from muscles.core import Column, Integer, Model, String
from muscles.core.schema.pydantic_bridge import pydantic_available
from muscles.core.schema.pydantic_bridge import to_json_schema
from muscles.core.schema.pydantic_bridge import to_pydantic_model
from muscles.core.schema.pydantic_bridge import from_pydantic_instance


class Booking(Model):
    columns = {
        "name": Column(String),
        "slots": Column(Integer),
    }


def test_to_json_schema_from_muscles_model():
    schema = to_json_schema(Booking)
    assert "Booking" in schema
    assert schema["Booking"]["type"] == "object"
    assert "name" in schema["Booking"]["properties"]


@pytest.mark.skipif(not pydantic_available(), reason="pydantic is optional and not installed")
def test_pydantic_bridge_roundtrip():
    PModel = to_pydantic_model(Booking)
    p_instance = PModel(name="Demo", slots=2)
    model = from_pydantic_instance(Booking, p_instance)

    assert model.name == "Demo"
    assert model.slots == 2
