from datetime import datetime

from pydantic_forms.utils.json import from_serializable


# Helper function for testing ISO formatted datetime
def test_from_serializable_datetime():
    iso_datetime = "2024-01-01T12:00:00+00:00"
    input_dict = {"timestamp": iso_datetime}
    expected_datetime = datetime.fromisoformat(iso_datetime)

    result = from_serializable(input_dict)

    assert isinstance(result["timestamp"], datetime)
    assert result["timestamp"] == expected_datetime


# Test that the function does not convert non-ISO format strings
def test_from_serializable_non_iso_string():
    input_dict = {"non_iso": "some random string"}

    result = from_serializable(input_dict)

    assert result["non_iso"] == "some random string"  # No conversion


# Test that no conversion happens if string is not in ISO format but looks similar
def test_from_serializable_non_iso_similar_string():
    similar_string = "2024-01-01 12:00:00"
    input_dict = {"similar_string": similar_string}

    result = from_serializable(input_dict)

    assert result["similar_string"] == similar_string  # No conversion


# Test handling of invalid ISO string that should not raise an error
def test_from_serializable_invalid_iso_string():
    invalid_iso = "2024-01-01T12:00:00"  # Missing timezone information
    input_dict = {"timestamp": invalid_iso}

    result = from_serializable(input_dict)

    assert result["timestamp"] == invalid_iso  # No conversion should happen


# Test multiple fields in dictionary, only ISO string should be converted
def test_from_serializable_mixed_dict():
    iso_datetime = "2024-01-01T12:00:00+00:00"
    input_dict = {
        "timestamp": iso_datetime,
        "non_iso": "hello",
        "integer": 42,
    }

    result = from_serializable(input_dict)

    # Check only the datetime field is converted
    assert isinstance(result["timestamp"], datetime)
    assert result["timestamp"] == datetime.fromisoformat(iso_datetime)
    assert result["non_iso"] == "hello"
    assert result["integer"] == 42


# Test that function handles empty dict correctly
def test_from_serializable_empty_dict():
    input_dict = {}

    result = from_serializable(input_dict)

    assert result == {}  # Should return an empty dict


# Test for non-string types
def test_from_serializable_non_string_values():
    input_dict = {
        "timestamp": "2024-01-01T12:00:00+00:00",
        "number": 123,
        "list": [1, 2, 3],
        "none_value": None,
    }

    result = from_serializable(input_dict)

    assert isinstance(result["timestamp"], datetime)
    assert result["number"] == 123
    assert result["list"] == [1, 2, 3]
    assert result["none_value"] is None


# Test when the timestamp is in a nested dictionary
def test_from_serializable_nested_dict():
    iso_datetime = "2024-01-01T12:00:00+00:00"
    input_dict = {"level1": {"timestamp": iso_datetime}}

    result = from_serializable(input_dict)

    # Since this function works on top-level only, the nested timestamp should not be converted
    assert result["level1"]["timestamp"] == iso_datetime  # No conversion
