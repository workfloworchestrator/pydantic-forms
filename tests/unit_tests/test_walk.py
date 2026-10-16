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
"""``walk_form``: ``post_form``'s walk, ending in the next page, the result, or the rejected page."""

import pytest
from pydantic import ValidationError

from pydantic_forms.core import Complete, FormPage, NextPage, Rejected, asynchronous, post_form, walk_form
from pydantic_forms.exceptions import FormValidationError


class First(FormPage):
    name: str


class Second(FormPage):
    count: int = 1


def two_pages(state):
    first = yield First
    second = yield Second
    return {**state, **first.model_dump(), **second.model_dump()}


async def two_pages_async(state):
    first = yield First
    second = yield Second
    yield {**state, **first.model_dump(), **second.model_dump()}


DONE = [{"name": "a"}, {"count": 2}]
BAD = [{"name": "a"}, {"count": "many"}]


def test_the_walk_ends_at_the_next_page_or_at_the_result_post_form_gives():
    assert walk_form(two_pages, {}, []) == NextPage(First, 0)
    assert walk_form(two_pages, {}, [{"name": "a"}]) == NextPage(Second, 1)
    assert walk_form(two_pages, {"reporter": "r"}, DONE) == Complete(post_form(two_pages, {"reporter": "r"}, DONE))
    assert walk_form(None, {"reporter": "r"}, []) == Complete({})


def test_a_rejected_page_is_named_with_the_verdict_post_form_raises():
    with pytest.raises(FormValidationError) as raised:
        post_form(two_pages, {}, BAD)
    rejected = walk_form(two_pages, {}, BAD)
    assert isinstance(rejected, Rejected)
    assert (rejected.model, rejected.index) == (Second, 1)
    assert rejected.error.errors == raised.value.errors  # the same verdict, translated the same way
    assert [(e["loc"], e["type"]) for e in rejected.error.errors] == [(("count",), "int_parsing")]
    assert isinstance(rejected.error.__cause__, ValidationError)  # chained as ``raise ... from`` chains it


async def test_the_async_walk_ends_the_same_way_with_the_result_yielded():
    assert await asynchronous.walk_form(two_pages_async, {}, []) == NextPage(First, 0)
    assert await asynchronous.walk_form(two_pages_async, {}, [{"name": "a"}]) == NextPage(Second, 1)
    assert await asynchronous.walk_form(two_pages_async, {"reporter": "r"}, DONE) == Complete(
        await asynchronous.post_form(two_pages_async, {"reporter": "r"}, DONE)
    )
    assert await asynchronous.walk_form(None, {}, []) == Complete({})
    rejected = await asynchronous.walk_form(two_pages_async, {}, BAD)
    assert isinstance(rejected, Rejected)
    assert (rejected.model, rejected.index) == (Second, 1)
    assert [(e["loc"], e["type"]) for e in rejected.error.errors] == [(("count",), "int_parsing")]
