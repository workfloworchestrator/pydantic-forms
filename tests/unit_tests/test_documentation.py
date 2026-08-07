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
"""Execute the code snippets in docs/ so the documentation cannot drift away from the API.

Every python and pycon fence on a page is run, in document order, against a single namespace, the
same way a reader working through the page from top to bottom would. A python fence is executed
for its side effects. A pycon fence is a console session run as a doctest, so the results printed
in the docs are asserted rather than merely produced. Note that blacken-docs already reformats
both kinds of fence, but it only parses them; it does not run them, so it catches none of the
errors this test does.

A snippet that is meant to illustrate rather than run can be excluded by putting the marker
"<!-- test: skip -->" on the line directly above its opening fence.

Top-level await is supported, so async snippets need no asyncio.run boilerplate.
"""

import ast
import asyncio
import doctest
import logging
from io import StringIO
from pathlib import Path
from typing import Any, NamedTuple

import pytest
import structlog
from markdown_it import MarkdownIt

from pydantic_forms.core.shared import FORMS
from tests.paths import ROOT

DOCS_DIR = ROOT / "docs"

# Languages we knowingly use in the docs. Anything else is most likely a typo in the fence
# (```py, ```pyhton), which would silently exclude a snippet from this test.
KNOWN_LANGUAGES = frozenset({"", "json", "python", "sh", "shell", "text", "yaml", "pycon"})

SKIP_MARKER = "<!-- test: skip -->"

# Fences we execute. A "python" fence is run for its side effects; a "pycon" fence is a console
# session that also asserts the results it prints, which is how the docs verify behaviour rather
# than merely not crashing.
PYTHON_LANGUAGES = frozenset({"python", "pycon"})

# A real CommonMark parser rather than a regex: it gets indented fences inside list items,
# tilde fences, and fences nested in a wider fence right, all of which a regex silently
# mis-reads -- and a missed snippet is one that quietly stops being tested.
MARKDOWN = MarkdownIt("commonmark")


class Snippet(NamedTuple):
    """A fenced code block, with the 1-based line number that its code starts on."""

    path: Path
    line: int
    lang: str
    skipped: bool
    code: str


def _is_skipped(lines: list[str], fence_line: int) -> bool:
    """Report whether the marker sits on the line directly above the opening fence."""
    return bool(fence_line) and lines[fence_line - 1].strip() == SKIP_MARKER


def _snippets(path: Path) -> list[Snippet]:
    text = path.read_text()
    lines = text.splitlines()
    fences = (token for token in MARKDOWN.parse(text) if token.type == "fence")
    return [
        Snippet(
            path=path,
            # token.map is [opening fence, closing fence], 0-based, so the code starts two lines on.
            line=token.map[0] + 2,
            lang=token.info.split()[0] if token.info.split() else "",
            skipped=_is_skipped(lines, token.map[0]),
            code=token.content,
        )
        for token in fences
    ]


def _runnable_python(path: Path) -> list[Snippet]:
    return [snippet for snippet in _snippets(path) if snippet.lang in PYTHON_LANGUAGES and not snippet.skipped]


def _run_source(snippet: Snippet, namespace: dict[str, Any]) -> None:
    """Execute a plain python fence for its side effects, such as defining a form."""
    # Pad with blank lines so that tracebacks and SyntaxErrors report the real line in the markdown file.
    source = "\n" * (snippet.line - 1) + snippet.code

    try:
        code = compile(source, str(snippet.path), "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    except SyntaxError as exc:
        raise AssertionError(f"{snippet.path.name}:{exc.lineno} does not compile: {exc.msg}") from exc

    try:
        # eval() rather than exec(), because a snippet using top-level await evaluates to a coroutine.
        coroutine = eval(code, namespace)  # noqa: S307
        if coroutine is not None:
            asyncio.run(coroutine)
    except Exception as exc:
        raise AssertionError(
            f"{snippet.path.name}:{snippet.line} raised {type(exc).__name__}: {exc}. Fix the snippet, "
            f"or put '<!-- test: skip -->' above its fence if it is only meant to illustrate."
        ) from exc


def _run_doctest(snippet: Snippet, namespace: dict[str, Any]) -> None:
    """Run a pycon fence as a doctest, checking that each result matches what the page claims."""
    test = doctest.DocTestParser().get_doctest(
        snippet.code,
        namespace,
        name=snippet.path.name,
        filename=str(snippet.path),
        lineno=snippet.line - 1,
    )
    # Without this, a fence whose lines all lack the prompt parses as one big block of expected
    # output, runs nothing, and passes -- the exact silent-skip this test exists to prevent.
    if not test.examples:
        raise AssertionError(
            f"{snippet.path.name}:{snippet.line} is a pycon fence with no doctest examples. "
            f"Every statement needs a '>>> ' prompt, and continuation lines a '... ' prompt."
        )

    report = StringIO()
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    # clear_globs=False so that names bound here stay visible to the rest of the page.
    result = runner.run(test, out=report.write, clear_globs=False)
    namespace.update(test.globs)

    if result.failed:
        raise AssertionError(f"{snippet.path.name}:{snippet.line} doctest failed:\n{report.getvalue()}")


def _run(snippet: Snippet, namespace: dict[str, Any]) -> None:
    match snippet.lang:
        case "pycon":
            _run_doctest(snippet, namespace)
        case _:
            _run_source(snippet, namespace)


def _doc_files() -> list[Path]:
    return sorted(DOCS_DIR.glob("*.md"))


def _doc_files_with_python() -> list[Path]:
    return [path for path in _doc_files() if _runnable_python(path)]


def _by_name(path: Path) -> str:
    return path.name


@pytest.fixture
def restore_form_registry():
    """Keep snippets that call register_form from leaking into the rest of the suite."""
    original = FORMS.copy()
    yield
    FORMS.clear()
    FORMS.update(original)


@pytest.fixture
def silence_logging():
    """Keep structlog off stdout, which doctest would otherwise compare as expected output."""
    original = structlog.get_config()
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL))
    yield
    structlog.configure(**original)


# These are called rather than passed as constants because parametrize needs its values at
# collection time, which is before any fixture could provide them.
@pytest.mark.parametrize("doc_file", _doc_files_with_python(), ids=_by_name)
def test_python_snippets_run(doc_file, restore_form_registry, silence_logging):
    namespace: dict[str, Any] = {"__name__": "__docs__"}
    for snippet in _runnable_python(doc_file):
        _run(snippet, namespace)


@pytest.mark.parametrize("doc_file", _doc_files(), ids=_by_name)
def test_fence_languages_are_known(doc_file):
    unknown = {snippet.lang for snippet in _snippets(doc_file)} - KNOWN_LANGUAGES
    assert not unknown, f"Unknown code fence language(s) {sorted(unknown)}; a typo here silently skips the snippet"


def test_docs_are_discovered():
    """Guard against the fence parsing silently matching nothing at all."""
    assert _doc_files(), f"No markdown files found in {DOCS_DIR}"
    assert _doc_files_with_python(), f"No runnable python snippets found in {DOCS_DIR}"
