# Test UUID serialization
from dataclasses import asdict, dataclass
from datetime import datetime
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from uuid import UUID

import pytest

from pydantic_forms.utils.json import to_serializable


def test_to_serializable_uuid():
    test_uuid = UUID("12345678123456781234567812345678")
    assert to_serializable(test_uuid) == str(test_uuid)


# Test IPv4 and IPv6 Address serialization
@pytest.mark.parametrize(
    "ip_address, expected",
    [
        (IPv4Address("192.168.1.1"), "192.168.1.1"),
        (IPv6Address("2001:db8::8a2e:370:7334"), "2001:db8::8a2e:370:7334"),
    ],
)
def test_to_serializable_ip_address(ip_address, expected):
    assert to_serializable(ip_address) == expected


# Test IPv4 and IPv6 Network serialization
@pytest.mark.parametrize(
    "ip_network, expected",
    [
        (IPv4Network("192.168.1.0/24"), "192.168.1.0/24"),
        (IPv6Network("2001:db8::/32"), "2001:db8::/32"),
    ],
)
def test_to_serializable_ip_network(ip_network, expected):
    assert to_serializable(ip_network) == expected


# Test datetime serialization
def test_to_serializable_datetime():
    test_datetime = datetime(2024, 1, 1)
    assert to_serializable(test_datetime) == "2024-01-01T00:00:00"


# Test dataclass serialization
@dataclass
class TestDataClass:
    id: int
    name: str


def test_to_serializable_dataclass():
    obj = TestDataClass(id=1, name="Test")
    assert to_serializable(obj) == asdict(obj)


# Test custom JSON method
class CustomJsonObject:
    def __json__(self):
        return {"custom": "json"}


def test_to_serializable_custom_json():
    obj = CustomJsonObject()
    assert to_serializable(obj) == {"custom": "json"}


# Test custom to_dict method
class CustomDictObject:
    def to_dict(self):
        return {"custom": "dict"}


def test_to_serializable_custom_dict():
    obj = CustomDictObject()
    assert to_serializable(obj) == {"custom": "dict"}


# Test set serialization
def test_to_serializable_set():
    test_set = {1, 2, 3}
    assert to_serializable(test_set) == list(test_set)


# Test ValueError and AssertionError serialization
@pytest.mark.parametrize(
    "exception, expected",
    [
        (ValueError("An error occurred"), "An error occurred"),
        (AssertionError("Assertion failed"), "Assertion failed"),
    ],
)
def test_to_serializable_exceptions(exception, expected):
    assert to_serializable(exception) == expected


# Test TypeError raised for unsupported types
def test_to_serializable_unsupported_type():
    class UnsupportedClass:
        pass

    obj = UnsupportedClass()
    with pytest.raises(TypeError, match="Could not serialize object of type UnsupportedClass to JSON"):
        to_serializable(obj)
