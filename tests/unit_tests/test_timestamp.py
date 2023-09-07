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
