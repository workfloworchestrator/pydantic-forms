from pydantic_forms.core import FormPage
from pydantic_forms.validators.components.markdown import MarkdownColor, markdown
from tests.unit_tests.helpers import PYDANTIC_VERSION


def test_markdown_default():
    """Ensure Markdown default is None and is unaffected by other field input."""
    MarkdownField = markdown(content="Hello world", color=MarkdownColor.PRIMARY)

    class Form(FormPage):
        name: str = "default"
        markdown_field: MarkdownField

    assert Form().model_dump() == {"name": "default", "markdown_field": None}
    assert Form(name="other").model_dump() == {"name": "other", "markdown_field": None}


def test_markdown_schema():
    """Ensure the markdown field generates a correct JSON schema with default data."""
    MarkdownField = markdown(content="Hello", color=MarkdownColor.PRIMARY)

    class Form(FormPage):
        markdown_field: MarkdownField

    if PYDANTIC_VERSION == "2.8":
        markdown_field_ref = {"allOf": [{"$ref": "#/$defs/MarkdownValue"}]}
    else:
        markdown_field_ref = {"$ref": "#/$defs/MarkdownValue"}

    expected = {
        "$defs": {"MarkdownValue": {"properties": {}, "title": "MarkdownValue", "type": "object"}},
        "additionalProperties": False,
        "properties": {
            "markdown_field": {
                **markdown_field_ref,
                "default": {
                    "content": "Hello",
                    "color": "primary",
                },
                "format": "markdown",
                "type": "string",
            },
        },
        "title": "unknown",
        "type": "object",
    }

    assert Form.model_json_schema() == expected


def test_markdown_accepts_custom_color():
    """Ensure custom (non-enum) color values are accepted and serialized correctly."""
    MarkdownField = markdown(content="Custom color", color="custom-blue")

    class Form(FormPage):
        markdown_field: MarkdownField

    schema = Form.model_json_schema()

    default_data = schema["properties"]["markdown_field"]["default"]
    assert default_data["color"] == "custom-blue"
    assert default_data["content"] == "Custom color"


def test_markdown_defaults_to_primary_color():
    """Ensure the default color is primary when not specified."""
    MarkdownField = markdown(content="No color specified")

    class Form(FormPage):
        markdown_field: MarkdownField

    schema = Form.model_json_schema()
    assert schema["properties"]["markdown_field"]["default"]["color"] == MarkdownColor.PRIMARY
