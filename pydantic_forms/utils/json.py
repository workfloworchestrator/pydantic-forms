# Copyright 2019-2025 SURF, ESnet.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Functions for custom serialization to and from JSON.

Both :func:`json.dumps` and :func:`json.loads` provide hooks for encoding and decoding objects they normally can't
encode and decode. Their hooks operate somewhat differently though.

:func:`json.dumps` has a `default` keyword argument that can be supplied with a function that will **only** be called
for objects it cannot encode. This function should return a new Python object (not a str in JSON format!) that can be
serialized to JSON by the active encoder. Generally this means that we should convert custom data types to either a
`str`, `int`, `float`, `bool` or a `dict` with only these primitive values. As the `default` function is a matter of
last resort it should raise a :exc:`TypeError` if it too can't encode an object. We have named the `default` function
:func:`to_serialize`.

To ensure we can decode what we have encoded we will include extra information about the custom data types, namely:

- the module the data type resides in
- the name of the data type

This information is encoded under the keys `"__module__"` and `"__class__"` respectively.

Upon decoding this information will be used to import the module and instantiate the class for the custom data
type dynamically. One obviously has to encode whatever information that's necessary to be able to decode it later as
well.

.. note:: There are libraries that provide this functionally out of the box. We have chosen not to use them as their
   means of encoding dumps the _internal_ representation of custom types. This can lead to fairly unreadable JSON. Eg.
   encoding a :obj:`uuid.UUID` object results in a large integer value plus an additional attribute `is_safe` that has
   no meaning to us. We, instead, want something that's human-readable as well.

.. warning:: Another thing to realize is that although we do encode :obj:`uuid.UUID` objects, we do not decode them.
   Past project decisions still haunt us, and we generally process UUIDs as `str`s in our backend, only converting them
   to real :obj:`uuid.UUID` objects where necessary. Don't simply assume UUID decoding logic was forgotten; it was not!

.. note:: Even though we do serialize domain models for audit log purposes to the state, we do not deserialize from
   the state. Instead we look them up in the DB instead (see: func:`server.utils.state.inject_args`). The reason for
   this decision is that we don't want to break currently running workflows when data models have their definition
   changed. If the database is the serialization store, we can deal with changes by means of DB data migrations. This
   is much, much harder to do when the serialization store is a JSON blob.

:func:`json.loads`'s hook works somewhat differently. Whereas the `default` function of :func:`json.dumps` is only
called as a matter of last resort, the `object_hook` function of :func:`json.loads is called for every `dict` value!
This means that, instead of raising an exception, it should return the `dict` that was passed in if it can't decode it.

The `object_hook` function will be called with the innermost `dict` first, working its way up to the top level `dict`.
Eg. Given::

    json_str = '{"a": 1, "b": 2, "c": {"x": true, "y": false}}'

The `object_hook` function will be called twice. First with the `dict`::

    {'x': True, 'y': False}

And then with the `dict`::

    {'a': 1, 'b': 2, 'c': {'x': True, 'y': False}}

:func:`json.loads` will replace the `dict` that it passed to `object_hook` function, with the object that the
`object_hook` function returned.

We have named the `object_hook` function :func:`from_serializable`. Reason for naming these custom encoding and
decoding functions differently then `default` and `object_hook` is that they are also used outside of the context of
:func:`json.dumps` and :func:`json.loads`.

"""
import re
from collections.abc import Callable
from contextlib import suppress
from dataclasses import asdict, is_dataclass
from datetime import datetime
from functools import partial
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network
from typing import Any, Sequence, Union
from uuid import UUID

import structlog
from pydantic import BaseModel

try:
    import orjson

    IS_ORJSON = True
except ImportError:
    import json

    IS_ORJSON = False


PY_JSON_TYPES = Union[dict[str, Any], list, str, int, float, bool, None, object]  # pragma: no mutate

logger = structlog.get_logger(__name__)


def to_serializable(o: Any) -> Any:
    """Convert an object into an object that the JSON encode can serialize.

    Args:
    ----
        o: Object to convert.

    Returns:
    -------
        Serializable object.

    Raises:
    ------
        TypeError: in case no conversion was possible.

    """
    if isinstance(o, UUID):
        return str(o)
    if (
        isinstance(o, IPv4Address)
        or isinstance(o, IPv6Address)
        or isinstance(o, IPv4Network)
        or isinstance(o, IPv6Network)
    ):
        return str(o)
    if isinstance(o, datetime):
        return isoformat(o)
    if is_dataclass(o):
        return asdict(o)  # type: ignore[arg-type]
    if hasattr(o, "__json__"):
        return o.__json__()
    if hasattr(o, "to_dict"):
        # api_client models all have a to_dict function
        return o.to_dict()
    if isinstance(o, BaseModel):
        return o.model_dump()
    if isinstance(o, set):
        return list(o)
    if isinstance(o, (ValueError, AssertionError)):
        return str(o)
    raise TypeError(f"Could not serialize object of type {o.__class__.__name__} to JSON")


ISO_FORMAT_STR_LEN = len("2019-05-18T15:17:00+00:00")  # assume 'seconds' precision
UUID_PATTERN = re.compile(r"^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$", re.IGNORECASE)


def from_serializable(dct: dict[str, Any]) -> dict[str, Any]:
    """Convert a serializable object into a more specific, custom, Python data type.

    Args:
    ----
        dct: Serializable object.

    Returns:
    -------
        Either the serializable object itself or a more specific data type if a conversion was possible.

    """
    for k, v in dct.items():
        # We don't want to try converting each string we come across to a `datetime` object, hence we employ a simple
        # and reasonably specific heuristic that identifies likely ISO formatted string candidates
        if isinstance(v, str) and len(v) == ISO_FORMAT_STR_LEN and v[10] == "T":
            with suppress(ValueError, TypeError):
                timestamp = datetime.fromisoformat(v)
                assert timestamp.tzinfo is not None, "All timestamps should contain timezone information."  # noqa: S101
                dct[k] = timestamp
    return dct


if IS_ORJSON:
    logger.debug("Using orjson")

    def json_loads(s: Union[str, bytes, bytearray]) -> PY_JSON_TYPES:
        o = orjson.loads(s)
        if isinstance(o, list):
            return [from_serializable(dikt) for dikt in o]
        return from_serializable(o)

    def json_dumps(obj: PY_JSON_TYPES, default: Callable = to_serializable) -> str:
        try:
            return orjson.dumps(
                obj,
                default=default,
                option=orjson.OPT_PASSTHROUGH_DATETIME | orjson.OPT_OMIT_MICROSECONDS | orjson.OPT_NON_STR_KEYS,
            ).decode("utf8")
        except TypeError as e:
            raise e

else:
    logger.debug("Using stdlib json")
    json_loads = json.loads
    json_dumps = partial(json.dumps, default=to_serializable)


def non_none_dict(dikt: Sequence[tuple[str, Any]]) -> dict[Any, Any]:
    """Return no `None` values in a Dict.

    This function may be used in the `asdict()` method as dictionary factory.

    Args:
    ----
        dikt: Tuple of values where

    Returns:
    -------
        dict of the keys and values if value is not None

    Examples:
    --------
        >>> non_none_dict({"a": 0, "b": None, "c": ""}.items())
        {'a': 0, 'c': ''}

    """
    return {k: v for k, v in dikt if v is not None}


def isoformat(dt: datetime) -> str:
    """ISO format datetime object with max precision limited to seconds.

    Args:
    ----
        dt: datatime object to be formatted

    Returns:
    -------
        ISO 8601 formatted string

    """
    # IMPORTANT should the format be ever changed, be sure to update TIMESTAMP_REGEX as well!
    return dt.isoformat(timespec="seconds")
