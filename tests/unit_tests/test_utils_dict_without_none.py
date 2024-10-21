from pydantic_forms.utils.json import non_none_dict


def test_basic_functionality():
    input_dict = {"a": 0, "b": None, "c": ""}.items()
    expected_output = {"a": 0, "c": ""}
    assert non_none_dict(input_dict) == expected_output


def test_all_none_values():
    input_dict = {"a": None, "b": None, "c": None}.items()
    expected_output = {}
    assert non_none_dict(input_dict) == expected_output


def test_no_none_values():
    input_dict = {"a": 1, "b": 2, "c": 3}.items()
    expected_output = {"a": 1, "b": 2, "c": 3}
    assert non_none_dict(input_dict) == expected_output


def test_empty_dict():
    input_dict = {}.items()
    expected_output = {}
    assert non_none_dict(input_dict) == expected_output


def test_mixed_data_types():
    input_dict = {"a": 1, "b": None, "c": [1, 2, 3], "d": ""}.items()
    expected_output = {"a": 1, "c": [1, 2, 3], "d": ""}
    assert non_none_dict(input_dict) == expected_output
