# Copyright 2019-2026 SURF.
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

"""The syntax of a JSON Pointer (RFC 6901) and of a Relative JSON Pointer, as published with JSON Schema 2020-12.

Parsing and escaping only. Where a pointer leads is decided by whoever holds the document, or the schema, it is
applied to; see ``pydantic_forms.utils.schema.resolve_pointer`` for the schema.
"""

import re
from typing import NamedTuple, Union


class Pointer(NamedTuple):
    """A parsed pointer: how many values up to start, then which members down."""

    levels_up: Union[int, None]
    """None for a JSON Pointer, which starts at the root; the integer prefix of a Relative JSON Pointer otherwise."""
    segments: tuple[str, ...]
    """The reference tokens, unescaped."""


_RELATIVE = re.compile(r"(0|[1-9][0-9]*)((?:/[^/]*)*)")


def parse_pointer(pointer: str) -> Union[Pointer, None]:
    """Split a JSON Pointer or a Relative JSON Pointer into levels up and segments down.

    ``"/a/b"`` starts at the root. ``"2/a"`` goes two values up, then into ``a``. Anything else gives None, including
    the relative form's ``#`` suffix, which names a member rather than a value.

    >>> parse_pointer("1/node")
    Pointer(levels_up=1, segments=('node',))
    >>> parse_pointer("/a~1b")
    Pointer(levels_up=None, segments=('a/b',))
    >>> parse_pointer("node") is None
    True
    """
    if pointer.startswith("/"):
        return Pointer(None, _segments(pointer))
    if match := _RELATIVE.fullmatch(pointer):
        return Pointer(int(match[1]), _segments(match[2]))
    return None


def _segments(pointer: str) -> tuple[str, ...]:
    return tuple(unescape(token) for token in pointer.split("/")[1:])


def unescape(token: str) -> str:
    """The member name a reference token stands for: ``~1`` is ``/`` and ``~0`` is ``~``, in that order.

    >>> unescape("a~1b~0c")
    'a/b~c'
    """
    return token.replace("~1", "/").replace("~0", "~")


def escape(name: str) -> str:
    """The reference token for a member name: ``~`` becomes ``~0`` and ``/`` becomes ``~1``.

    >>> escape("a/b~c")
    'a~1b~0c'
    """
    return name.replace("~", "~0").replace("/", "~1")
