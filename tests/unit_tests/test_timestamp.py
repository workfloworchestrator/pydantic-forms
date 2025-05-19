from contextlib import nullcontext

import pytest
from pydantic import TypeAdapter, ValidationError

from pydantic_forms.core import FormPage
from pydantic_forms.validators import Timestamp, timestamp


def test_timestamp_schema():
    class Form(FormPage):
        t1: Timestamp
        t2: timestamp(
            locale="nl-nl", min=1652751600, max=1672751600, date_format="DD-MM-YYYY HH:mm", time_format="HH:mm"  # noqa
        )

    expected = {
        "additionalProperties": False,
        "properties": {
            "t1": {
                "format": "timestamp",
                "title": "T1",
                "type": "number",
                "uniforms": {
                    "dateFormat": None,
                    "locale": None,
                    "max": None,
                    "min": None,
                    "showTimeSelect": True,
                    "timeFormat": None,
                },
            },
            "t2": {
                "format": "timestamp",
                "maximum": 1672751600,
                "minimum": 1652751600,
                "title": "T2",
                "type": "number",
                "uniforms": {
                    "dateFormat": "DD-MM-YYYY HH:mm",
                    "locale": "nl-nl",
                    "max": 1672751600,
                    "min": 1652751600,
                    "showTimeSelect": True,
                    "timeFormat": "HH:mm",
                },
            },
        },
        "required": ["t1", "t2"],
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected


@pytest.mark.parametrize(
    "min_value,max_value,input_value,validate,expectation",
    [
        (1652751600, 1652751601, 1652751599, True, pytest.raises(ValidationError, match="greater")),
        (1652751600, 1652751601, 1652751600, True, nullcontext(1652751600)),
        (1652751600, 1652751601, 1652751601, True, nullcontext(1652751601)),
        (1652751600, 1652751601, 1652751602, True, pytest.raises(ValidationError, match="less")),
        (1652751600, None, 1652751600, True, nullcontext(1652751600)),
        (1652751600, None, 1652751599, True, pytest.raises(ValidationError, match="greater")),
        (1652751600, None, 1652751599, False, nullcontext(1652751599)),  # backwards compatibility
    ],
)
def test_timestamp_validation(min_value, max_value, input_value, validate, expectation):
    adapter = TypeAdapter(timestamp(min=min_value, max=max_value, validate=validate))

    with expectation as expected_result:
        assert adapter.validate_python(input_value) == expected_result
