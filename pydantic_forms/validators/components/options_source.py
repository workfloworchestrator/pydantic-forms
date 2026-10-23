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
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema

from pydantic_forms.utils.pointer import parse_pointer
from pydantic_forms.utils.schema import DEPENDS_ON, OPTIONS_SOURCE

# A ``{name}`` in the url, filled by the client with the value ``depends_on[name]`` points at.
_PLACEHOLDER = re.compile(r"\{([^{}]*)\}")


@dataclass(frozen=True)
class OptionsSource:
    """Say where a field's options are fetched, e.g. `Annotated[str, OptionsSource(url="/api/locations")]`.

    Adds a camelCase `optionsSource` object to the field's JSON schema, beside whatever the type already carries
    (its `format`, a `Layout`). A client that renders or fills the form calls the URL with the person's
    credentials and offers the response as the field's options; this library only describes the request.
    The URL carries its own query string, written the way the route reads it; a client fills the placeholders,
    appends `search` when declared, and fetches. On a list field the source describes the options of its items.

    Args:
        url: Relative to the API that serves the form, or absolute, query string included. A `{name}` placeholder,
            in the path or the query string, is filled with the URL-encoded value `depends_on[name]` points at.
        search: Name of the query parameter that narrows the list on the server. Without it a client fetches
            the list once and filters it itself.
        items: JSON pointer to the list inside the response, such as `"/data/customers"`. Without it the
            response is the list.
        value: Key of an item that is the field's value. Without it the item itself is, as for a list of strings.
        label: Key of an item, or a `{key}` template such as `"{fullname} ({shortcode})"`, shown to a person.
            Without it the value is shown.
        depends_on: Where the value of each `{name}` in the url is read from while the page is filled in, as a
            pointer into the page's data: a JSON pointer from the page, `"/service_speed"`, or a relative JSON
            pointer from this field's own value, `"1/node"` for the `node` beside it in the same object. A pointer
            is a path, so the same name at two depths is never confused. Until every one has a value the field
            has no options yet.
    """

    url: str
    search: str | None = None
    items: str | None = None
    value: str | None = None
    label: str | None = None
    depends_on: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.url:
            raise ValueError("url must not be empty")
        if self.items is not None and not self.items.startswith("/"):
            raise ValueError("items must be a JSON pointer, which starts with '/'")
        placeholders = set(_PLACEHOLDER.findall(self.url))
        pointers = dict(self.depends_on or {})
        if unmapped := placeholders - pointers.keys():
            raise ValueError(f"url names {sorted(unmapped)}, which depends_on does not map to a field")
        if unused := pointers.keys() - placeholders:
            raise ValueError(f"depends_on maps {sorted(unused)}, which url does not name")
        if invalid := {name: pointer for name, pointer in pointers.items() if parse_pointer(pointer) is None}:
            raise ValueError(f"depends_on {invalid} is not a JSON pointer or a relative JSON pointer")

    def __get_pydantic_json_schema__(self, core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        keys: dict[str, Any] = {
            "url": self.url,
            "search": self.search,
            "items": self.items,
            "value": self.value,
            "label": self.label,
            DEPENDS_ON: dict(self.depends_on) if self.depends_on else None,
        }
        source = {key: value for key, value in keys.items() if value is not None}
        return handler(core_schema) | {OPTIONS_SOURCE: source}
